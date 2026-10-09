#!/usr/bin/env python3
"""PostToolUse hook for Write: opens a newly created plan file in VS Code.
Matches ~/.claude/plans/<repo>/<YYYY-MM-DD>-<desc>/<desc>_plan.md.
Rewrites of an existing plan do not open it again.
"""
import json
import os
import re
import subprocess
import sys

def main():
    data = json.load(sys.stdin)
    file_path = data.get("tool_input", {}).get("file_path", "")
    if data.get("tool_response", {}).get("type") != "create":
        return
    base = os.path.join(os.path.expanduser("~"), ".claude", "plans") + os.sep
    if not file_path.startswith(base):
        return
    parts = file_path[len(base):].split(os.sep)
    if len(parts) == 3 and re.match(r"^\d{4}-\d{2}-\d{2}-.+", parts[1]) and parts[2].endswith("_plan.md"):
        subprocess.Popen(["code", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
