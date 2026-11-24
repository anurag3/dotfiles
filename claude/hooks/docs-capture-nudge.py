#!/usr/bin/env python3
"""Stop hook: once per session, nudges Claude to record new repo facts in <repo>/.docs/.
Fires only if the repo has a .docs/ folder and the session edited a file in the repo
outside .docs/ (read from the transcript) or moved HEAD. State is kept per session in a temp file.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time


def git(cwd, *args):
    res = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3)
    return res.stdout if res.returncode == 0 else None


EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
STATE_MAX_AGE = 7 * 86400


def edited_in_repo(transcript, root):
    docs = os.path.join(root, ".docs")
    try:
        with open(transcript) as f:
            for line in f:
                try:
                    msg = json.loads(line)
                    if msg.get("type") != "assistant":
                        continue
                    for block in msg["message"]["content"]:
                        if block.get("type") != "tool_use" or block.get("name") not in EDIT_TOOLS:
                            continue
                        inp = block.get("input") or {}
                        path = inp.get("file_path") or inp.get("notebook_path")
                        if not path:
                            continue
                        path = os.path.realpath(path)
                        if path.startswith(root + os.sep) and not path.startswith(docs + os.sep):
                            return True
                except (ValueError, AttributeError, KeyError, TypeError):
                    continue
    except OSError:
        pass
    return False


def prune(state_dir):
    cutoff = time.time() - STATE_MAX_AGE
    for name in os.listdir(state_dir):
        if name.endswith(".json"):
            try:
                path = os.path.join(state_dir, name)
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except OSError:
                pass


def main():
    try:
        data = json.load(sys.stdin)
        if data.get("stop_hook_active"):
            return
        if data.get("permission_mode") == "plan":
            return

        root = (git(data.get("cwd") or ".", "rev-parse", "--show-toplevel") or "").strip()
        root = os.path.realpath(root) if root else ""
        if not root or not os.path.isdir(os.path.join(root, ".docs")):
            return

        state_dir = os.environ.get("DOCS_CAPTURE_NUDGE_STATE_DIR") or os.path.join(
            tempfile.gettempdir(), "docs-capture-nudge")
        os.makedirs(state_dir, exist_ok=True)
        prune(state_dir)
        sid = re.sub(r"[^A-Za-z0-9_.-]", "_", str(data.get("session_id") or "unknown"))
        state_path = os.path.join(state_dir, sid + ".json")
        try:
            with open(state_path) as f:
                state = json.load(f)
        except (OSError, ValueError):
            state = {}
        if state.get("nudged"):
            return

        head = (git(root, "rev-parse", "HEAD") or "").strip()
        stored = state.get("head")
        changed = (bool(stored) and head != stored) or edited_in_repo(data.get("transcript_path") or "", root)

        with open(state_path, "w") as f:
            json.dump({"head": stored or head, "nudged": changed}, f)
        if changed:
            reason = (
                f"This session changed code in {os.path.basename(root)}, which has local .docs/ notes. "
                "If the session found a durable fact about this repo (a gotcha, a bug, a data or code flow "
                "detail), run /repo-docs capture. Otherwise stop."
            )
            print(json.dumps({"decision": "block", "reason": reason}))
    except Exception:
        return


if __name__ == "__main__":
    main()
