#!/usr/bin/env python3
"""PreToolUse guard for Write: enforces the plan-file-location skill's path
convention (~/.claude/plans/<repo>/<YYYY-MM-DD>-<desc>/<desc>_plan.md) so a
misplaced plan file is rejected at write-time instead of relying on the model
to remember to invoke the skill.
"""
import json
import os
import re
import sys

def main():
    data = json.load(sys.stdin)
    file_path = data.get("tool_input", {}).get("file_path", "")
    base = os.path.join(os.path.expanduser("~"), ".claude", "plans") + os.sep
    if not file_path.startswith(base):
        return

    rel = file_path[len(base):]
    parts = rel.split(os.sep)
    # Nested convention: <repo>/<YYYY-MM-DD>-<desc>/<desc>_plan.md
    nested = len(parts) >= 3 and re.match(r"^\d{4}-\d{2}-\d{2}-.+", parts[1])
    # Flat form assigned by Claude Code's own plan-mode harness: plans/<slug>.md
    flat = len(parts) == 1 and parts[0].endswith(".md")
    if nested or flat:
        return

    reason = (
        "Blocked: plan files must live at "
        "~/.claude/plans/<repo>/<YYYY-MM-DD>-<plan_description>/<plan_description>_plan.md "
        f"(got: {file_path}). Invoke the plan-file-location skill to derive the correct "
        "repo/date/description and mkdir -p that path before writing — do this even if "
        "plan mode was already active with no EnterPlanMode tool call."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))

if __name__ == "__main__":
    main()
