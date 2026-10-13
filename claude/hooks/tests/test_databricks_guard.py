import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "databricks-guard.py"


def run_hook(stdin):
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, check=True)


def decision(command):
    out = run_hook(json.dumps({"tool_name": "Bash", "cwd": "/", "tool_input": {"command": command}})).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else "allow"


COMMIT_HEREDOC = """git commit -m "$(cat <<'EOF'
docs: explain dbt run
EOF
)\""""

DENY = [
    "databricks bundle deploy",
    "databricks --profile PROD bundle deploy",
    "databricks -p PROD jobs run-now 123",
    "databricks bundle -t prod deploy",
    "databricks bundle destroy",
    "databricks bundle validate",
    "databricks jobs submit --json @run.json",
    "databricks api post /api/2.1/jobs/run-now",
    "/opt/homebrew/bin/databricks bundle deploy",
    "env FOO=1 databricks bundle run my_job",
    "echo hi && dbt run",
    "dbt --debug run",
    "uv run dbt build",
    "poetry run dbt test -s my_model",
    "dbt show --inline 'select 1'",
    "bash -c 'dbt run'",
    "echo ALLOW_DATABRICKS_RUN=1 && databricks bundle deploy",
    'databricks experimental aitools tools query "SELECT * FROM t"',
    "databricks experimental aitools tools query --profile PROD 'select a from t'",
    "databricks experimental aitools tools query \"SELECT * FROM t WHERE note = 'limit 5'\"",
    'databricks bundle deploy "unclosed',
    'echo "$(dbt run)"',
    "eval databricks bundle deploy",
    "nice -n 5 dbt run",
    "timeout 60 databricks bundle run job",
    "echo x | xargs dbt run",
    "find . -name '*.sql' -exec databricks bundle deploy \\;",
    "find . -name '*.sql' -execdir dbt run {} \\;",
    "uvx dbt run",
    "python -m dbt run",
    "uv run --frozen dbt run",
    "uv run --directory proj dbt run",
    "uv run --project dbt dbt run",
    "databricks warehouses create --name w",
    "databricks apps create my-app",
    "databricks clusters edit 123",
    "databricks api POST /api/2.1/jobs/run-now",
    'databricks experimental aitools tools query "SELECT a FROM t -- limit 10"',
    'databricks experimental aitools tools query "SELECT a FROM t /* limit 10 */"',
    'databricks experimental aitools tools query --warehouse abc "SELECT * FROM t"',
]

ALLOW = [
    "ls",
    'gh pr create --title "fix: x" --body "Ran dbt test"',
    'git commit -m "docs: explain dbt run"',
    COMMIT_HEREDOC,
    "grep -r 'databricks bundle deploy' .",
    "dbt deps",
    "dbt --version",
    "dbt ls",
    "databricks bundle --help",
    "ALLOW_DATABRICKS_RUN=1 databricks bundle deploy",
    'databricks experimental aitools tools query "SELECT * FROM t LIMIT 10"',
    'databricks experimental aitools tools query "DESCRIBE TABLE t"',
    'databricks experimental aitools tools query "SELECT count(*) FROM t"',
    "echo 'unclosed",
    "uv run --directory dbt pytest",
    "uv run --project dbt dbt deps",
    "poetry -C dbt run pytest",
    "python3 -m pytest dbt tests/",
    "find dbt -name '*.sql'",
    "find . -name dbt",
    "find . -type d -name databricks",
    'databricks experimental aitools tools query "SELECT * FROM t LIMIT 10 OFFSET 5"',
    'databricks experimental aitools tools query --warehouse-id abc "SELECT 1 LIMIT 1"',
    'databricks experimental aitools tools query --warehouse abc "SELECT 1 LIMIT 1"',
    "dbt run --help",
    "databricks bundle deploy --help",
    'git commit -m "fix: \\`dbt run\\`"',
]


class Guard(unittest.TestCase):
    def test_deny(self):
        for cmd in DENY:
            self.assertEqual(decision(cmd), "deny", cmd)

    def test_allow(self):
        for cmd in ALLOW:
            self.assertEqual(decision(cmd), "allow", cmd)

    def test_query_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as handle:
            handle.write("SELECT * FROM t LIMIT 5")
        for flag in (f"--file {handle.name}", f"--file={handle.name}"):
            self.assertEqual(decision(f"databricks experimental aitools tools query {flag}"), "allow", flag)
        Path(handle.name).unlink()

    def test_non_string_command_denies(self):
        out = run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": 5}}))
        self.assertEqual(out.stderr, "")
        self.assertEqual(json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_bad_json_denies(self):
        out = run_hook("not json").stdout
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
