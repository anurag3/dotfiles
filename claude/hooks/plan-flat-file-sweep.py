#!/usr/bin/env python3
"""Stop hook: finds flat plan files (~/.claude/plans/<slug>.md) and blocks the stop
so Claude moves each one to the nested path from CLAUDE.md rule 6.
Plan mode writes the flat files, and plan-file-location-guard.py allows them.
"""
import glob
import json
import os
import sys

def main():
    data = json.load(sys.stdin)
    # Stop once after one nudge. Prevents a loop if Claude cannot move a file.
    if data.get("stop_hook_active"):
        return

    plans = os.path.join(os.path.expanduser("~"), ".claude", "plans")
    flat = sorted(glob.glob(os.path.join(plans, "*.md")))
    if not flat:
        return

    names = ", ".join(os.path.basename(p) for p in flat)
    reason = (
        f"Flat plan files found in ~/.claude/plans/: {names}. "
        "For each file: 1. Find its repo and a 2-5 word kebab-case description from its content. "
        "2. If a nested plan with identical content exists (cmp), delete the flat file. "
        "3. Otherwise mkdir -p ~/.claude/plans/<repo>/<YYYY-MM-DD>-<description>/ and mv the file to "
        "<description>_plan.md there. Use the file's modification date for the date."
    )
    print(json.dumps({"decision": "block", "reason": reason}))

if __name__ == "__main__":
    main()
