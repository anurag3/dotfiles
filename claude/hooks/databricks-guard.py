#!/usr/bin/env python3
"""PreToolUse guard for Bash: enforces global CLAUDE.md rules 9 (Databricks
Command Confirmation) and 10 (Sample Before Querying Databricks Tables) at
hook time instead of relying on the model to remember them.

Blocks, unless the escape hatch is present:
  - Databricks CLI ops that run a job/pipeline/deploy or start billable
    compute: `databricks bundle deploy`, `databricks bundle run`,
    `databricks jobs run-now`, `databricks pipelines start-update`,
    `databricks warehouses start`, `databricks clusters start`.
  - `dbt run` / `dbt build` / `dbt test` / `dbt seed`, however invoked
    (bare, `uv run dbt ...`, `poetry run dbt ...`, etc).
  - `databricks experimental aitools tools query "<SQL>"` when the SQL is an
    unbounded row-level scan: no LIMIT, no DESCRIBE, no SHOW, and not a plain
    aggregate (COUNT/SUM/MIN/MAX/AVG or GROUP BY).

Escape hatch: include ALLOW_DATABRICKS_RUN=1 anywhere in the command string
to bypass this guard once the human has approved the run.
"""
import json
import re
import sys

ESCAPE_HATCH = "ALLOW_DATABRICKS_RUN=1"

# Databricks CLI operations that trigger a real job/pipeline/deploy or spin
# up billable compute against a live workspace.
CLI_PATTERNS = [
    re.compile(r"databricks\s+bundle\s+deploy\b"),
    re.compile(r"databricks\s+bundle\s+run\b"),
    re.compile(r"databricks\s+jobs\s+run-now\b"),
    re.compile(r"databricks\s+pipelines\s+start-update\b"),
    re.compile(r"databricks\s+warehouses\s+start\b"),
    re.compile(r"databricks\s+clusters\s+start\b"),
]

# dbt subcommands that execute against the configured target, however
# invoked. Lookahead (not \b) on the tail so "run-operation" doesn't match
# "run".
DBT_PATTERN = re.compile(r"\bdbt\s+(run|build|test|seed)(?=\s|$)")

AITOOLS_QUERY_PATTERN = re.compile(
    r"databricks\s+experimental\s+aitools\s+tools\s+query\s*(.*)$", re.S
)

AGGREGATE_SELECT = re.compile(r"^\s*[\"']?\s*select\s+(count|sum|min|max|avg)\b", re.I)


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def is_unbounded_scan(sql_arg: str) -> bool:
    """True if this aitools-query SQL looks like an unbounded row-level scan
    rather than a bounded sample, a schema check, or a plain aggregate."""
    sql = sql_arg.strip()
    if re.search(r"\blimit\b", sql, re.I):
        return False
    if re.search(r"\bdescribe\b", sql, re.I):
        return False
    if re.search(r"\bshow\b", sql, re.I):
        return False
    if AGGREGATE_SELECT.match(sql):
        return False
    if re.search(r"\bgroup\s+by\b", sql, re.I):
        return False
    return True


def main() -> None:
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return

    if ESCAPE_HATCH in command:
        return

    for pattern in CLI_PATTERNS:
        if pattern.search(command):
            deny(
                "[BLOCKED] This Databricks CLI command runs a job/pipeline/deploy "
                "or starts billable compute against a live workspace. Confirm "
                "with the human before running it (CLAUDE.md rule 9: Databricks "
                f"Command Confirmation). If already approved, re-run with "
                f"{ESCAPE_HATCH} prefixed to the command."
            )

    if DBT_PATTERN.search(command):
        deny(
            "[BLOCKED] dbt run/build/test/seed executes against a live "
            "Databricks target, even when it looks read-only. Confirm with "
            "the human before running it (CLAUDE.md rule 9: Databricks "
            f"Command Confirmation). If already approved, re-run with "
            f"{ESCAPE_HATCH} prefixed to the command."
        )

    aitools_match = AITOOLS_QUERY_PATTERN.search(command)
    if aitools_match and is_unbounded_scan(aitools_match.group(1)):
        deny(
            "[BLOCKED] This SQL has no LIMIT/DESCRIBE/SHOW and is not a "
            "plain aggregate. Confirm the table's structure first "
            "(discover-schema / DESCRIBE TABLE), then sample with SELECT * "
            "... LIMIT 10 (CLAUDE.md rule 10: Sample Before Querying "
            f"Databricks Tables). If already approved, re-run with "
            f"{ESCAPE_HATCH} prefixed to the command."
        )


if __name__ == "__main__":
    main()
