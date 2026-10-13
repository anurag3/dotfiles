#!/usr/bin/env python3
"""PreToolUse guard for Write: enforces CLAUDE.md rule 6 for plans and specs.

1. Denies a plan or spec file that is not at the rule 6 path.
2. Denies writes to docs/superpowers/plans/ and docs/superpowers/specs/.
3. Replaces the superpowers subagent-driven-development header in a plan
   with the executing-plans-in-waves header (CLAUDE.md rule 5).
"""
import json
import os
import re
import sys

DATED = re.compile(r"^\d{4}-\d{2}-\d{2}-.+")
PLAN_TEMPLATE = "~/.claude/plans/<repo>/<YYYY-MM-DD>-<description>/<description>_plan.md"
SPEC_TEMPLATE = "~/.claude/specs/<repo>/<YYYY-MM-DD>-<description>/<description>_spec.md"
SDD_MARKER = "REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development"
WAVES_HEADER = (
    "> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans-in-waves "
    "to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking."
)


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def in_dated_dir(parts):
    return len(parts) >= 3 and bool(DATED.match(parts[1]))


# Contract from https://code.claude.com/docs/en/hooks (PreToolUse decision control):
# hookSpecificOutput.updatedInput replaces the entire tool input, so it must
# include file_path and content. It applies with permissionDecision "allow" or
# "ask". This hook uses "allow", so this Write gets no permission prompt.
# The hook sends "allow" only for valid plan and spec paths.
# Deny and ask rules in settings still apply to the new input.
def rewrite_header(content):
    lines = content.split("\n")
    return "\n".join(WAVES_HEADER if SDD_MARKER in line else line for line in lines)


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        file_path = os.path.normpath(tool_input.get("file_path", ""))

        if "/docs/superpowers/plans/" in file_path or "/docs/superpowers/specs/" in file_path:
            deny(
                f"Blocked: {file_path} is a superpowers default path. CLAUDE.md rule 6 requires "
                f"plans at {PLAN_TEMPLATE} and specs at {SPEC_TEMPLATE}. "
                "Make the directory with mkdir -p, then write the file there."
            )
            return

        claude = os.path.join(os.path.expanduser("~"), ".claude")
        plans = os.path.join(claude, "plans") + os.sep
        specs = os.path.join(claude, "specs") + os.sep

        if file_path.startswith(plans):
            parts = file_path[len(plans):].split(os.sep)
            # parts == 1 is the plan mode file. parts == 2 is a handoff note.
            allowed = (len(parts) in (1, 2) and parts[-1].endswith(".md")) or in_dated_dir(parts)
            template = PLAN_TEMPLATE
        elif file_path.startswith(specs):
            allowed = in_dated_dir(file_path[len(specs):].split(os.sep))
            template = SPEC_TEMPLATE
        else:
            return

        if not allowed:
            deny(
                f"Blocked: {file_path} does not match the CLAUDE.md rule 6 path {template}. "
                "Find the repo, date, and description, make the directory with mkdir -p, "
                "then write the file there. Do this also when plan mode was active "
                "without an EnterPlanMode tool call."
            )
            return

        content = tool_input.get("content")
        if isinstance(content, str):
            new_content = rewrite_header(content)
            if new_content != content:
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "permissionDecisionReason": "Replaced the superpowers execution header (CLAUDE.md rule 5).",
                        "updatedInput": dict(tool_input, content=new_content),
                    }
                }))
    except Exception:
        return


if __name__ == "__main__":
    main()
