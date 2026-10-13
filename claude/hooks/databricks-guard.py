#!/usr/bin/env python3
"""PreToolUse guard for Bash: enforces global CLAUDE.md rules 9 (Databricks
Command Confirmation) and 10 (Sample Before Querying Databricks Tables).

Checks each simple command after wrappers (`env`, `nice`, `timeout`,
`bash -c`, `eval`, `$(...)`, absolute path). Blocks, unless the escape hatch
is present:
  - Databricks CLI commands that deploy, run, or start billable compute, also
    with global flags such as `--profile X`: `bundle deploy`, `bundle run`,
    `bundle destroy`, `bundle validate`, `jobs run-now`, `jobs submit`,
    `jobs repair-run`, `pipelines start-update`, `warehouses start`,
    `warehouses create`, `clusters start`, `clusters create`, `clusters edit`,
    `apps create`, `apps deploy`, `apps start`, and `api post|put|patch|delete`.
  - Each dbt subcommand that connects to a target, direct or through a
    runner (`uv run dbt ...`, `poetry run dbt ...`, `python -m dbt ...`).
    `deps`, `clean`, `parse`, `ls`, `list`, and `init` are allowed.
  - `databricks experimental aitools tools query` when the SQL is an
    unbounded row-level scan: no final LIMIT n (with an optional OFFSET m),
    not DESCRIBE or SHOW, and not a plain aggregate. SQL comments are ignored.
  - `xargs`, `watch`, or `parallel` with `databricks` or `dbt` in their
    arguments, and `find` with them after `-exec`, `-execdir`, `-ok`, or
    `-okdir`. The parser does not read into these commands.

A quoted mention, for example in a commit message or a grep pattern, is not
a command and is allowed. A `databricks` or `dbt` command with `-h` or
`--help` only shows help and is allowed.

Escape hatch: set ALLOW_DATABRICKS_RUN=1 as an env assignment on the same
simple command, after the human approves the run. The assignment does not
go into a nested script. For `bash -c '...'`, put the assignment inside the
script: `bash -c 'ALLOW_DATABRICKS_RUN=1 dbt run'`.

Fails closed: if the hook input cannot be read, it denies. If the command
cannot be parsed, it denies only when the command contains `databricks` or
`dbt`.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import cmdparse  # noqa: E402

ESCAPE_HATCH = "ALLOW_DATABRICKS_RUN=1"

DATABRICKS_VALUE_FLAGS = {"-p", "--profile", "-o", "--output", "-t", "--target",
                          "--log-level", "--log-file", "--log-format", "--var"}
BLOCKED_CLI = {
    ("bundle", "deploy"), ("bundle", "run"), ("bundle", "destroy"), ("bundle", "validate"),
    ("jobs", "run-now"), ("jobs", "submit"), ("jobs", "repair-run"),
    ("pipelines", "start-update"), ("warehouses", "start"), ("warehouses", "create"),
    ("clusters", "start"), ("clusters", "create"), ("clusters", "edit"),
    ("apps", "create"), ("apps", "deploy"), ("apps", "start"),
}
# Flag names from the Databricks plugin docs. The CLI help was not read, because rule 9 needs approval for it.
AITOOLS_VALUE_FLAGS = DATABRICKS_VALUE_FLAGS | {"--warehouse", "--warehouse-id"}
API_WRITE = {"post", "put", "patch", "delete"}
DBT_RUNNERS = {"uv", "uvx", "poetry", "pipenv", "pdm", "hatch", "python", "python3"}
# A `dbt` token after one of these runner flags is a directory or package name, not the dbt command.
RUNNER_VALUE_FLAGS = {"--directory", "--project", "--with", "--python", "-p", "--package",
                      "--env-file", "--group", "--extra", "-C", "-e", "--env", "--from"}
FIND_EXEC = {"-exec", "-execdir", "-ok", "-okdir"}
HELP_FLAGS = {"-h", "--help"}
DBT_SAFE = {"deps", "clean", "parse", "ls", "list", "init"}
DBT_VALUE_FLAGS = {"--profiles-dir", "--project-dir", "--target", "-t", "--log-path",
                   "--target-path", "--log-level", "--profile", "--vars"}
TRIGGER = re.compile(r"\b(databricks|dbt)\b")

AGGREGATE_SELECT = re.compile(r"^\s*[\"']?\s*select\s+(count|sum|min|max|avg)\b", re.I)

CLI_MESSAGE = (
    "[BLOCKED] This Databricks CLI command runs a job/pipeline/deploy "
    "or starts billable compute against a live workspace. Confirm "
    "with the human before running it (CLAUDE.md rule 9: Databricks "
    f"Command Confirmation). If already approved, re-run with "
    f"{ESCAPE_HATCH} prefixed to the command."
)
DBT_MESSAGE = (
    "[BLOCKED] This dbt command connects to a live Databricks target, "
    "even when it looks read-only. Confirm with "
    "the human before running it (CLAUDE.md rule 9: Databricks "
    f"Command Confirmation). If already approved, re-run with "
    f"{ESCAPE_HATCH} prefixed to the command."
)
SQL_MESSAGE = (
    "[BLOCKED] This SQL has no LIMIT/DESCRIBE/SHOW and is not a "
    "plain aggregate. Confirm the table's structure first "
    "(discover-schema / DESCRIBE TABLE), then sample with SELECT * "
    "... LIMIT 10 (CLAUDE.md rule 10: Sample Before Querying "
    "Databricks Tables). Invoke the sampling-databricks-tables "
    f"skill first. If already approved, re-run with "
    f"{ESCAPE_HATCH} prefixed to the command."
)


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def dbt_args(argv):
    """Return the args after `dbt` for a direct or runner call (`uv run dbt ...`), else None."""
    if argv[0] == "dbt":
        return argv[1:]
    if argv[0] not in DBT_RUNNERS:
        return None
    for i in range(1, len(argv)):
        if argv[i] != "dbt":
            continue
        if argv[0].startswith("python"):
            found = argv[i - 1] == "-m"
        else:
            found = argv[i - 1] not in RUNNER_VALUE_FLAGS and (
                argv[0] == "uvx" or {"run", "exec"} & set(argv[1:i]))
        if found:
            return argv[i + 1:]
    return None


def runner_args(argv):
    """Return the args that a runner can execute. For `find`, only the args after `-exec` and similar."""
    if argv[0] != "find":
        return argv[1:]
    start = next((i for i, arg in enumerate(argv) if arg in FIND_EXEC), len(argv))
    return argv[start + 1:]


def query_sql(args, cwd):
    """Return the SQL of an aitools query, or None when it cannot be read."""
    for i, arg in enumerate(args):
        path = arg[len("--file="):] if arg.startswith("--file=") else (
            args[i + 1] if arg in ("--file", "-f") and i + 1 < len(args) else None)
        if path is not None:
            try:
                with open(os.path.join(cwd, os.path.expanduser(path))) as handle:
                    return handle.read()
            except (OSError, UnicodeDecodeError):
                return None
    rest = cmdparse.positionals(args, AITOOLS_VALUE_FLAGS)[4:]
    return rest[0] if rest else None


def is_unbounded_scan(sql):
    """True unless the SQL ends in LIMIT n [OFFSET m], starts with DESCRIBE/SHOW, or is a plain aggregate."""
    # Remove string literals before comments, so that `'limit 5'` and `'--'` are not read as SQL.
    bare = re.sub(r"'(?:[^']|'')*'", "''", sql)
    bare = re.sub(r"--[^\n]*|/\*.*?\*/", " ", bare, flags=re.S).strip()
    if re.search(r"\blimit\s+\d+(\s+offset\s+\d+)?\s*;?\s*$", bare, re.I):
        return False
    if re.match(r"^\s*(describe|desc|show)\b", bare, re.I):
        return False
    if AGGREGATE_SELECT.match(bare) or re.search(r"\bgroup\s+by\b", bare, re.I):
        return False
    return True


def main() -> None:
    try:
        data = json.load(sys.stdin)
        if data.get("tool_name") != "Bash":
            return
        command = data.get("tool_input", {}).get("command", "")
        if not isinstance(command, str):
            raise TypeError("tool_input.command is not a string")
        cwd = data.get("cwd") or os.getcwd()
    except Exception as exc:
        # Fail closed: a hook that can't parse its own input is not a check
        # that the model can route around by sending it something odd.
        deny(f"[BLOCKED] databricks-guard could not parse hook input ({exc}); "
             "denying by default. Re-run manually after confirming with the "
             "human, or investigate the malformed tool call.")
        return

    if not command:
        return

    try:
        commands = cmdparse.simple_commands(command)
    except ValueError:
        if TRIGGER.search(command):
            deny(CLI_MESSAGE)
        return

    for env, argv, _ in commands:
        if env.get("ALLOW_DATABRICKS_RUN") == "1":
            continue
        if argv[0] in cmdparse.RUNNERS and any(
                os.path.basename(arg) in ("databricks", "dbt") for arg in runner_args(argv)):
            deny(CLI_MESSAGE)
        if argv[0] == "databricks" and not HELP_FLAGS & set(argv[1:]):
            pos = cmdparse.positionals(argv[1:], DATABRICKS_VALUE_FLAGS)
            if tuple(pos[:2]) in BLOCKED_CLI or (pos[:1] == ["api"] and pos[1:2] and pos[1].lower() in API_WRITE):
                deny(CLI_MESSAGE)
            if pos[:4] == ["experimental", "aitools", "tools", "query"]:
                sql = query_sql(argv[1:], cwd)
                if sql is None or is_unbounded_scan(sql):
                    deny(SQL_MESSAGE)
        args = dbt_args(argv)
        if args is not None and not HELP_FLAGS & set(args):
            sub = cmdparse.positionals(args, DBT_VALUE_FLAGS)[:1]
            if sub and sub[0] not in DBT_SAFE:
                deny(DBT_MESSAGE)


if __name__ == "__main__":
    main()
