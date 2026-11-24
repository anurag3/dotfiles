import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "docs-capture-nudge.py"
GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env=GIT_ENV)


class Nudge(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.mkdtemp()
        self.repo = Path(tempfile.mkdtemp()) / "myrepo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("a")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "init")

    def run_hook(self, payload, sid="s1"):
        if isinstance(payload, dict):
            payload = dict({"session_id": sid, "cwd": str(self.repo)}, **payload)
            payload = json.dumps(payload)
        env = dict(os.environ, DOCS_CAPTURE_NUDGE_STATE_DIR=self.state)
        return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, env=env)

    def assertSilent(self, res):
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))

    def docs(self):
        (self.repo / ".docs").mkdir(exist_ok=True)
        (self.repo / ".docs" / "n.md").write_text("n")

    def transcript(self, *edits):
        path = Path(self.state) / "t.jsonl"
        lines = ["not json"]
        for name, file_path in edits:
            key = "notebook_path" if name == "NotebookEdit" else "file_path"
            lines.append(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "x"}, {"type": "tool_use", "name": name, "input": {key: str(file_path)}}]}}))
        path.write_text("\n".join(lines) + "\n")
        return {"transcript_path": str(path)}

    def assertBlock(self, res):
        out = json.loads(res.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertEqual(out["reason"], (
            "This session changed code in myrepo, which has local .docs/ notes. If the session found a "
            "durable fact about this repo (a gotcha, a bug, a data or code flow detail), run /repo-docs "
            "capture. Otherwise stop."))

    def test_no_docs_dir(self):
        self.assertSilent(self.run_hook(self.transcript(("Edit", self.repo / "a.txt"))))

    def test_preexisting_dirty_tree_no_edits(self):
        self.docs()
        (self.repo / "a.txt").write_text("dirty before session")
        self.assertSilent(self.run_hook(self.transcript()))

    def test_edit_in_repo_blocks(self):
        self.docs()
        self.assertBlock(self.run_hook(self.transcript(("Edit", self.repo / "a.txt"))))

    def test_notebook_edit_blocks(self):
        self.docs()
        self.assertBlock(self.run_hook(self.transcript(("NotebookEdit", self.repo / "n.ipynb"))))

    def test_edit_only_docs_silent(self):
        self.docs()
        self.assertSilent(self.run_hook(self.transcript(("Write", self.repo / ".docs" / "x.md"))))

    def test_edit_outside_repo_silent(self):
        self.docs()
        self.assertSilent(self.run_hook(self.transcript(("Edit", Path(self.state) / "other.txt"))))

    def test_second_stop_after_block_silent(self):
        self.docs()
        extra = self.transcript(("Edit", self.repo / "a.txt"))
        self.assertBlock(self.run_hook(extra))
        self.assertSilent(self.run_hook(extra))

    def test_missing_transcript_head_moved_blocks(self):
        self.docs()
        gone = {"transcript_path": str(Path(self.state) / "missing.jsonl")}
        self.assertSilent(self.run_hook(gone))
        (self.repo / "a.txt").write_text("changed")
        git(self.repo, "commit", "-q", "-am", "more")
        self.assertBlock(self.run_hook(gone))

    def test_missing_transcript_clean_silent(self):
        self.docs()
        self.assertSilent(self.run_hook({"transcript_path": "/nonexistent.jsonl"}))

    def test_old_state_pruned(self):
        self.docs()
        old = Path(self.state) / "old.json"
        old.write_text("{}")
        past = time.time() - 8 * 86400
        os.utime(old, (past, past))
        self.assertSilent(self.run_hook({}))
        self.assertFalse(old.exists())

    def test_stop_hook_active(self):
        self.docs()
        self.assertSilent(self.run_hook(dict(self.transcript(("Edit", self.repo / "a.txt")), stop_hook_active=True)))

    def test_plan_mode(self):
        self.docs()
        self.assertSilent(self.run_hook(dict(self.transcript(("Edit", self.repo / "a.txt")), permission_mode="plan")))

    def test_non_repo_cwd(self):
        self.assertSilent(self.run_hook(dict(self.transcript(("Edit", self.repo / "a.txt")), cwd=tempfile.mkdtemp())))

    def test_bad_json(self):
        self.assertSilent(self.run_hook("not json"))


if __name__ == "__main__":
    unittest.main()
