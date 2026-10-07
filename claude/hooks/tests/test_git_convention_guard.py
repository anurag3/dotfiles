import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "git-convention-guard.py"


def run_hook(stdin: str) -> str:
    result = subprocess.run(
        [sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, check=True
    )
    return result.stdout


def decision(command: str, cwd: str = "/") -> str:
    out = run_hook(json.dumps({"tool_name": "Bash", "cwd": cwd, "tool_input": {"command": command}}))
    if not out.strip():
        return "allow"
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


def reason(command: str) -> str:
    out = run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
    return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


HEREDOC_OK = """git commit -m "$(cat <<'EOF'
feat: add guard hook

Adds a hook that checks "commit" messages.
EOF
)\""""

HEREDOC_BAD = """git add a.py && git commit -m "$(cat <<'EOF'
feat: add guard hook

Generated with Claude Code
EOF
)\""""


class CommitTests(unittest.TestCase):
    def test_valid_subject_allowed(self):
        self.assertEqual(decision('git commit -m "fix: correct null check in foo()"'), "allow")

    def test_scope_and_breaking_allowed(self):
        self.assertEqual(decision("git commit -m 'feat(api)!: drop v1 routes'"), "allow")

    def test_bad_subject_denied(self):
        self.assertEqual(decision('git commit -m "Fixed the thing"'), "deny")
        self.assertIn("rule 12", reason('git commit -m "Fixed the thing"'))

    def test_unknown_type_denied(self):
        self.assertEqual(decision('git commit -m "update: things"'), "deny")

    def test_long_message_flag_and_equals_form(self):
        self.assertEqual(decision('git commit --message "nope"'), "deny")
        self.assertEqual(decision('git commit --message="docs: fix typo"'), "allow")

    def test_combined_short_flags(self):
        self.assertEqual(decision('git commit -am "nope"'), "deny")
        self.assertEqual(decision('git commit -am "chore: bump deps"'), "allow")

    def test_multiple_messages_body_checked(self):
        cmd = 'git commit -m "fix: x" -m "Co-Authored-By: Claude <noreply@anthropic.com>"'
        self.assertEqual(decision(cmd), "deny")
        self.assertIn("rule 13", reason(cmd))
        self.assertEqual(decision('git commit -m "fix: x" -m "Handles empty input."'), "allow")

    def test_banned_patterns_denied(self):
        for body in [
            "see ~/.claude/plans/foo/bar_plan.md",
            "spec in ~/.claude/specs/x",
            "Task 3 done",
            "after fix round 2",
            "done per the plan",
            "found by ponytail",
            "Generated with Claude Code",
        ]:
            with self.subTest(body=body):
                self.assertEqual(decision(f'git commit -m "fix: x" -m "{body}"'), "deny")

    def test_heredoc_allowed_and_denied(self):
        self.assertEqual(decision(HEREDOC_OK), "allow")
        self.assertEqual(decision(HEREDOC_BAD), "deny")

    def test_no_message_flag_allowed(self):
        self.assertEqual(decision("git commit"), "allow")
        self.assertEqual(decision("git commit -F msg.txt"), "allow")
        self.assertEqual(decision("git commit --amend --no-edit"), "allow")

    def test_rtk_prefix(self):
        self.assertEqual(decision('rtk git commit -m "bad subject"'), "deny")
        self.assertEqual(decision('rtk git commit -m "test: add cases"'), "allow")

    def test_git_global_options_and_chaining(self):
        self.assertEqual(decision('git -C /tmp/repo commit -m "bad"'), "deny")
        self.assertEqual(decision('cd x && git add . && git commit -m "bad"'), "deny")
        self.assertEqual(decision('cd x && git add . && git commit -m "ci: x"'), "allow")

    def test_mention_in_other_command_allowed(self):
        self.assertEqual(decision("echo 'git commit -m bad'"), "allow")
        self.assertEqual(decision("git log --grep 'ponytail'"), "allow")


class BranchTests(unittest.TestCase):
    def test_checkout_b(self):
        self.assertEqual(decision("git checkout -b fix/null-check-in-foo"), "allow")
        self.assertEqual(decision("git checkout -b my-branch"), "deny")
        self.assertIn("rule 12", reason("git checkout -b my-branch"))

    def test_switch_c(self):
        self.assertEqual(decision("git switch -c feat/new-hook main"), "allow")
        self.assertEqual(decision("git switch -c Feat/New"), "deny")

    def test_branch_create(self):
        self.assertEqual(decision("git branch chore/cleanup"), "allow")
        self.assertEqual(decision("git branch wip"), "deny")

    def test_branch_non_create_allowed(self):
        for cmd in ["git branch", "git branch -d wip", "git branch -D wip", "git branch --list", "git branch -a"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(decision(cmd), "allow")

    def test_branch_ponytail_denied(self):
        self.assertEqual(decision("git checkout -b chore/ponytail-cleanup"), "deny")

    def test_rtk_prefix(self):
        self.assertEqual(decision("rtk git checkout -b wip"), "deny")

    def test_plain_checkout_allowed(self):
        self.assertEqual(decision("git checkout main"), "allow")
        self.assertEqual(decision("git switch main"), "allow")


class PrTests(unittest.TestCase):
    def test_title(self):
        self.assertEqual(decision('gh pr create --title "feat: add hook" --body "Adds a hook."'), "allow")
        self.assertEqual(decision('gh pr create --title "Add hook" --body "x"'), "deny")
        self.assertEqual(decision('gh pr create -t "Add hook" -b "x"'), "deny")
        self.assertEqual(decision('gh pr create --title="fix: y"'), "allow")

    def test_body_banned(self):
        cmd = 'gh pr create --title "feat: x" --body "Implements Task 3 per the plan"'
        self.assertEqual(decision(cmd), "deny")
        self.assertIn("rule 13", reason(cmd))
        self.assertEqual(decision('gh pr create -t "feat: x" -b "Generated with Claude Code"'), "deny")

    def test_heredoc_body(self):
        cmd = """gh pr create --title "feat: x" --body "$(cat <<'EOF'
## Summary
- adds x

Generated with Claude Code
EOF
)\""""
        self.assertEqual(decision(cmd), "deny")

    def test_fill_allowed(self):
        self.assertEqual(decision("gh pr create --fill"), "allow")

    def test_rtk_prefix(self):
        self.assertEqual(decision('rtk gh pr create --title "nope" --body "x"'), "deny")


class InputTests(unittest.TestCase):
    def test_malformed_stdin_allowed(self):
        self.assertEqual(run_hook("not json").strip(), "")

    def test_unparseable_command_allowed(self):
        self.assertEqual(decision('git commit -m "unterminated'), "allow")

    def test_unresolved_expansion_allowed(self):
        self.assertEqual(decision('git commit -m "$MSG"'), "allow")
        self.assertEqual(decision('git commit -m "$(printf "feat: x")"'), "allow")
        self.assertEqual(decision('gh pr create --title "$TITLE" --body "x"'), "allow")

    def test_other_tool_ignored(self):
        out = run_hook(json.dumps({"tool_name": "Write", "tool_input": {"command": 'git commit -m "bad"'}}))
        self.assertEqual(out.strip(), "")


class FixRoundOneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name: str, text: str) -> str:
        path = Path(self.tmp.name) / name
        path.write_text(text)
        return str(path)

    def test_attribution_variants_denied(self):
        for body in [
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)",
            "Co-authored-by:Claude <x@y>",
            "Co-Authored-By: Someone <noreply@anthropic.com>",
        ]:
            with self.subTest(body=body):
                self.assertEqual(decision(f'git commit -m "fix: x" -m "{body}"'), "deny")

    def test_plain_heredoc_body_not_parsed_as_command(self):
        cmd = """cat > notes.md <<'EOF'
git commit -m "WIP"
EOF
echo done"""
        self.assertEqual(decision(cmd), "allow")

    def test_plain_heredoc_then_bad_commit_denied(self):
        cmd = """cat > notes.md <<'EOF'
text
EOF
git commit -m "WIP\""""
        self.assertEqual(decision(cmd), "deny")

    def test_commit_file(self):
        good = self.write("good.txt", "feat: add x\n\nBody.\n")
        bad = self.write("bad.txt", "WIP\n")
        banned = self.write("banned.txt", "fix: x\n\nGenerated with Claude Code\n")
        self.assertEqual(decision(f"git commit -F {good}"), "allow")
        self.assertEqual(decision(f"git commit -F {bad}"), "deny")
        self.assertEqual(decision(f"git commit --file={banned}"), "deny")
        self.assertEqual(decision("git commit -F bad.txt", cwd=self.tmp.name), "deny")
        self.assertEqual(decision("git commit -F /no/such/file"), "allow")

    def test_commit_file_stdin_heredoc(self):
        bad = """git commit -F - <<'EOF'
WIP
EOF"""
        good = """git commit -F - <<'EOF'
docs: update readme
EOF"""
        self.assertEqual(decision(bad), "deny")
        self.assertEqual(decision(good), "allow")
        self.assertEqual(decision("git commit -F -"), "allow")

    def test_trailer_banned(self):
        self.assertEqual(decision('git commit -m "fix: x" --trailer "Co-authored-by: Claude <a@b>"'), "deny")
        self.assertEqual(decision('git commit -m "fix: x" --trailer "Reviewed-by: Ann <a@b>"'), "allow")

    def test_force_create_branch_forms(self):
        self.assertEqual(decision("git checkout -B wip"), "deny")
        self.assertEqual(decision("git checkout -B fix/x"), "allow")
        self.assertEqual(decision("git switch -C wip"), "deny")
        self.assertEqual(decision("git switch --create=wip"), "deny")
        self.assertEqual(decision("git switch --create wip"), "deny")
        self.assertEqual(decision("git switch --create=feat/x"), "allow")

    def test_branch_rename_checks_new_name(self):
        self.assertEqual(decision("git branch -m old wip"), "deny")
        self.assertEqual(decision("git branch -M wip fix/x"), "allow")
        self.assertEqual(decision("git branch -m wip"), "deny")

    def test_git_global_options(self):
        self.assertEqual(decision('git --git-dir /tmp/r/.git commit -m "bad"'), "deny")
        self.assertEqual(decision('git -c user.name=x commit -m "bad"'), "deny")
        self.assertEqual(decision('git -C /tmp/r -c a=b commit -m "test: x"'), "allow")

    def test_commit_file_relative_to_git_c(self):
        self.write("bad.txt", "WIP\n")
        self.assertEqual(decision(f"git -C {self.tmp.name} commit -F bad.txt"), "deny")

    def test_gh_pr_edit(self):
        self.assertEqual(decision('gh pr edit 12 --title "Add hook"'), "deny")
        self.assertEqual(decision('gh pr edit 12 --body "Generated with Claude Code"'), "deny")
        self.assertEqual(decision('gh pr edit 12 --title "feat: add hook"'), "allow")

    def test_gh_body_file(self):
        banned = self.write("body.md", "## Summary\nDone per the plan.\n")
        good = self.write("ok.md", "## Summary\nAdds x.\n")
        self.assertEqual(decision(f'gh pr create -t "feat: x" --body-file {banned}'), "deny")
        self.assertEqual(decision(f'gh pr create -t "feat: x" -F {good}'), "allow")
        self.assertEqual(decision('gh pr create -t "feat: x" --body-file /no/such.md'), "allow")

    def test_task_bookkeeping_only(self):
        self.assertEqual(decision('git commit -m "feat: add Task 1 scheduler"'), "allow")
        for body in ["Task 3", "Task 3: done", "(Task 3) wiring", "Task 2 of 5", "  task 4 complete"]:
            with self.subTest(body=body):
                self.assertEqual(decision(f'git commit -m "fix: x" -m "{body}"'), "deny")

    def test_ponytail_still_banned(self):
        self.assertEqual(decision('git commit -m "chore: tidy" -m "ponytail cleanup"'), "deny")

    def test_scope_characters(self):
        self.assertEqual(decision('git commit -m "fix(api/v2.users_db): x"'), "allow")
        self.assertEqual(decision('git commit -m "fix(Core): x"'), "allow")
        self.assertEqual(decision('git commit -m "fix(a b): x"'), "deny")

    def test_revert_and_autosquash_prefixes(self):
        for subject in [
            'Revert "feat: add x"',
            "fixup! fix: y",
            "squash! docs: z",
            "amend! test: w",
            'fixup! Revert "feat: add x"',
        ]:
            with self.subTest(subject=subject):
                self.assertEqual(decision(f"git commit -m '{subject}'"), "allow")
        for subject in ['Revert "add x"', "fixup! add y", "fixup!fix: y"]:
            with self.subTest(subject=subject):
                self.assertEqual(decision(f"git commit -m '{subject}'"), "deny")


if __name__ == "__main__":
    unittest.main()
