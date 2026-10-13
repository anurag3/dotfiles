import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cmdparse  # noqa: E402


def argvs(command):
    return [argv for _, argv, _ in cmdparse.simple_commands(command)]


class SimpleCommands(unittest.TestCase):
    def test_chain(self):
        self.assertEqual(argvs("echo hi && dbt run; ls | wc"), [["echo", "hi"], ["dbt", "run"], ["ls"], ["wc"]])

    def test_env_prefix_kept(self):
        env, argv, _ = cmdparse.simple_commands("ALLOW_DATABRICKS_RUN=1 databricks bundle deploy")[0]
        self.assertEqual(env, {"ALLOW_DATABRICKS_RUN": "1"})
        self.assertEqual(argv, ["databricks", "bundle", "deploy"])

    def test_wrappers_dropped(self):
        self.assertEqual(argvs("env -i FOO=1 git status"), [["git", "status"]])
        self.assertEqual(argvs("command git status"), [["git", "status"]])
        self.assertEqual(argvs("nohup git status"), [["git", "status"]])

    def test_absolute_path_basename(self):
        self.assertEqual(argvs("/usr/bin/git status"), [["git", "status"]])

    def test_shell_c_recursion(self):
        self.assertEqual(argvs("bash -c 'git add . && dbt run'"), [["git", "add", "."], ["dbt", "run"]])
        self.assertEqual(argvs("sh -lc \"git status\""), [["git", "status"]])

    def test_quoted_text_is_one_arg(self):
        self.assertEqual(argvs('gh pr create --body "Ran dbt test"'), [["gh", "pr", "create", "--body", "Ran dbt test"]])

    def test_unbalanced_quote_raises(self):
        with self.assertRaises(ValueError):
            cmdparse.simple_commands("echo 'oops")


class Bypasses(unittest.TestCase):
    PUSH = ["git", "push", "-f"]

    def test_wrapper_value_flags(self):
        self.assertEqual(argvs("env -u NAME git reset --hard"), [["git", "reset", "--hard"]])
        for cmd in ("nice -n 10 git status", "sudo -u root git status", "timeout 5 git status",
                    "env -C /tmp git status", "exec -a x git status", "stdbuf -oL git status",
                    "doas -u root git status", "timeout -s KILL 5 git status"):
            self.assertEqual(argvs(cmd), [["git", "status"]], cmd)

    def test_env_split_string(self):
        self.assertEqual(argvs("env -S 'FOO=1 git push -f'"), [self.PUSH])

    def test_hash_is_not_a_comment(self):
        self.assertIn(self.PUSH, argvs("echo issue#1; git push -f"))

    def test_quoted_heredoc_marker(self):
        try:
            self.assertIn(self.PUSH, argvs("echo '<<X'\ngit push -f\nX"))
        except ValueError:
            pass

    def test_literal_placeholder_raises(self):
        with self.assertRaises(ValueError):
            cmdparse.simple_commands("echo __ARG7__")

    def test_shell_keywords(self):
        for cmd in ("{ git push -f; }", "if true; then git push -f; fi", "! git push -f",
                    "while true; do git push -f; done"):
            self.assertIn(self.PUSH, argvs(cmd), cmd)

    def test_command_substitution(self):
        for cmd in ('echo "$(git push -f)"', "echo `git push -f`", 'echo "$(echo $(git push -f))"'):
            self.assertIn(self.PUSH, argvs(cmd), cmd)
        self.assertIn(["echo", "x"], argvs('echo "$(git push -f)" && echo x'))

    def test_escaped_backtick_not_substitution(self):
        self.assertEqual([argv[:2] for argv in argvs('git commit -m "fix: \\`git push -f\\`"')],
                         [["git", "commit"]])
        # `\\` is an escaped backslash. The backtick after it starts a substitution.
        self.assertIn(self.PUSH, argvs("echo \\\\`git push -f`"))

    def test_quoted_heredoc_body_not_scanned(self):
        cmd = "git commit -m \"$(cat <<'EOF'\nfix: x\n\nUse `don't` here.\nEOF\n)\""
        self.assertEqual(argvs(cmd)[0][:3], ["git", "commit", "-m"])

    def test_shell_c_double_dash(self):
        self.assertIn(self.PUSH, argvs("bash -c -- 'git push -f'"))

    def test_shell_heredoc_stdin(self):
        self.assertIn(self.PUSH, argvs("bash <<EOF\ngit push -f\nEOF"))

    def test_eval(self):
        self.assertIn(self.PUSH, argvs("eval git push -f"))

    def test_too_deep_raises(self):
        with self.assertRaises(ValueError):
            cmdparse.simple_commands('eval eval eval eval eval git push -f')

    def test_runners_exported(self):
        self.assertEqual(cmdparse.RUNNERS, {"xargs", "find", "watch", "parallel"})


class Helpers(unittest.TestCase):
    def test_positionals(self):
        self.assertEqual(cmdparse.positionals(["-p", "PROD", "bundle", "-t", "x", "deploy"], {"-p", "-t"}), ["bundle", "deploy"])
        self.assertEqual(cmdparse.positionals(["a", "--", "-b"], set()), ["a", "-b"])

    def test_split_git(self):
        self.assertEqual(cmdparse.split_git(["-C", "x", "-c", "k=v", "reset", "--hard"]), (["x"], "reset", ["--hard"]))
        self.assertEqual(cmdparse.split_git(["--version"]), ([], None, []))

    def test_split_gh(self):
        self.assertEqual(cmdparse.split_gh(["-R", "o/r", "pr", "create"]), ["pr", "create"])
