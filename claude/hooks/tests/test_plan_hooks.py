import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
SDD = ("> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development "
       "(recommended) or superpowers:executing-plans to implement this plan task-by-task. "
       "Steps use checkbox (`- [ ]`) syntax for tracking.")


class Base(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.plans = os.path.join(self.home, ".claude", "plans")
        self.specs = os.path.join(self.home, ".claude", "specs")
        os.makedirs(self.plans)

    def run_hook(self, name, payload, path=None):
        env = dict(os.environ, HOME=self.home)
        if path:
            env["PATH"] = path
        stdin = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run([sys.executable, str(HOOKS / name)], input=stdin,
                              capture_output=True, text=True, env=env)

    def guard(self, file_path, content="x"):
        res = self.run_hook("plan-file-location-guard.py",
                            {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}})
        self.assertEqual(res.returncode, 0, res.stderr)
        return json.loads(res.stdout)["hookSpecificOutput"] if res.stdout.strip() else None


class LocationGuard(Base):
    def test_allowed(self):
        for rel in ("plans/dotfiles/2026-10-12-x/x_plan.md", "plans/dotfiles/2026-10-12-x/progress.md",
                    "plans/flat.md", "plans/dotfiles/handoff.md", "specs/dotfiles/2026-10-12-x/x_spec.md",
                    "plans/dotfiles/2026-10-12-x/sub/deep.md", "plans/dotfiles/2026-10-12-x/notes.txt",
                    "plans/dotfiles/2026-10-12-x/registry.py", "plans/dotfiles/2026-10-12-x/page.raw.json",
                    "plans/dotfiles/2026-10-12-x/confluence/diagrams/flow.mmd",
                    "specs/dotfiles/2026-10-12-x/assets/diagram.html"):
            self.assertIsNone(self.guard(os.path.join(self.home, ".claude", rel)), rel)
        self.assertIsNone(self.guard("/tmp/other.md"))

    def test_normalizes_path(self):
        self.assertIsNone(self.guard(os.path.join(self.plans, "..", "..", "evil.md")))

    def test_denied(self):
        for rel in ("plans/dotfiles/undated/y_plan.md", "plans/dotfiles/undated/deep/x.md",
                    "specs/dotfiles/foo.md", "specs/dotfiles/undated/deep/x.md"):
            out = self.guard(os.path.join(self.home, ".claude", rel))
            self.assertEqual(out and out["permissionDecision"], "deny", rel)
        for path in ("/repo/docs/superpowers/plans/2026-10-12-x.md",
                     "/repo/docs/superpowers/specs/2026-10-12-x-design.md"):
            self.assertEqual(self.guard(path)["permissionDecision"], "deny", path)

    def test_rewrites_sdd_header(self):
        path = os.path.join(self.plans, "dotfiles", "2026-10-12-x", "x_plan.md")
        out = self.guard(path, f"# X\n\n{SDD}\n\nbody\n")
        content = out["updatedInput"]["content"]
        self.assertIn("executing-plans-in-waves", content)
        self.assertNotIn("subagent-driven-development", content)
        self.assertEqual(out["updatedInput"]["file_path"], path)

    def test_bad_json_guard(self):
        res = self.run_hook("plan-file-location-guard.py", "not json")
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))


class Sweep(Base):
    def flat(self, age_seconds):
        path = os.path.join(self.plans, "slug.md")
        Path(path).write_text("x")
        old = time.time() - age_seconds
        os.utime(path, (old, old))

    def test_sweep_blocks_old_file(self):
        self.flat(3600)
        res = self.run_hook("plan-flat-file-sweep.py", {"stop_hook_active": False})
        self.assertEqual(json.loads(res.stdout)["decision"], "block")

    def test_sweep_skips_recent_file(self):
        self.flat(60)
        self.assertEqual(self.run_hook("plan-flat-file-sweep.py", {}).stdout, "")

    def test_sweep_skips_plan_mode(self):
        self.flat(3600)
        self.assertEqual(self.run_hook("plan-flat-file-sweep.py", {"permission_mode": "plan"}).stdout, "")

    def test_bad_json_sweep(self):
        res = self.run_hook("plan-flat-file-sweep.py", "not json")
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))


class OpenInVSCode(Base):
    def test_missing_code_cli(self):
        path = os.path.join(self.plans, "dotfiles", "2026-10-12-x", "x_plan.md")
        res = self.run_hook("plan-open-in-vscode.py",
                            {"tool_input": {"file_path": path}, "tool_response": {"type": "create"}},
                            path="/nonexistent")
        self.assertEqual((res.returncode, res.stderr), (0, ""))

    def test_bad_json_open(self):
        res = self.run_hook("plan-open-in-vscode.py", "not json")
        self.assertEqual((res.returncode, res.stderr), (0, ""))
