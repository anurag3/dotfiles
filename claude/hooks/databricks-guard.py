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

Escape hatch: prefix the command with ALLOW_DATABRICKS_RUN=1 (a real leading
env-var assignment, not the text appearing anywhere in the command) to bypass
this guard once the human has approved the run.
"""
import json
import re
import sys

ESCAPE_HATCH = "ALLOW_DATABRICKS_RUN=1"

# Anchored to the start of the command so the escape hatch can't be smuggled
# into an unrelated part of the command (e.g. a quoted SQL argument or a
# trailing comment) — it must actually be the leading env-var assignment.
ESCAPE_HATCH_PATTERN = re.compile(r"^\s*ALLOW_DATABRICKS_RUN=1(?=\s|$)")

# Databricks CLI operations that trigger a real job/pipeline/deploy or spin
# up billable compute against a live workspace.
CLI_PATTERNS = [
    re.compile(r"databricks\s+bundle\s+deploy\b", re.I),
    re.compile(r"databricks\s+bundle\s+run\b", re.I),
    re.compile(r"databricks\s+jobs\s+run-now\b", re.I),
    re.compile(r"databricks\s+pipelines\s+start-update\b", re.I),
    re.compile(r"databricks\s+warehouses\s+start\b", re.I),
    re.compile(r"databricks\s+clusters\s+start\b", re.I),
]

# dbt subcommands that execute against the configured target, however
# invoked. Lookahead (not \b) on the tail so "run-operation" doesn't match
# "run".
DBT_PATTERN = re.compile(r"\bdbt\s+(run|build|test|seed)(?=\s|$)", re.I)

# Captures only the SQL argument itself — the quoted string right after
# "query" (stopping at the matching closing quote), or a single bare token
# (e.g. a file.sql path) — not any trailing shell content (";  # comment",
# "&& echo done", "| grep ...") after it.
AITOOLS_QUERY_PATTERN = re.compile(
    r"databricks\s+experimental\s+aitools\s+tools\s+query\s+"
    r"(?:(?P<quote>[\"'])(?P<quoted>.*?)(?P=quote)|(?P<bare>\S+))",
    re.S,
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
    try:
        data = json.load(sys.stdin)
        if data.get("tool_name") != "Bash":
            return
        command = data.get("tool_input", {}).get("command", "")
    except Exception as exc:
        # Fail closed: a hook that can't parse its own input is not a check
        # that the model can route around by sending it something odd.
        deny(f"[BLOCKED] databricks-guard could not parse hook input ({exc}); "
             "denying by default. Re-run manually after confirming with the "
             "human, or investigate the malformed tool call.")
        return

    if not command:
        return

    if ESCAPE_HATCH_PATTERN.match(command):
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
    sql_arg = aitools_match.group("quoted") if aitools_match and aitools_match.group("quoted") is not None \
        else (aitools_match.group("bare") if aitools_match else None)
    if sql_arg is not None and is_unbounded_scan(sql_arg):
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
