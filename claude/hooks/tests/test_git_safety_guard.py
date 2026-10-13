import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "git-safety-guard.py"


def decision(command, implementer=False, raw=None):
    args = [sys.executable, str(HOOK)] + (["--implementer"] if implementer else [])
    stdin = raw if raw is not None else json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    out = subprocess.run(args, input=stdin, capture_output=True, text=True, check=True).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else "allow"


ALWAYS_DENY = [
    "git push --force", "git push -f origin x", "git push -uf origin x",
    "git push --force-with-lease", "git push origin +main",
    "git reset --hard", "git -C . reset --hard HEAD~1", "env git reset --hard",
    "git clean -fd", "git -c x=y clean -xfd", "git clean --force",
    "git branch -D old", "git branch -d -f old", "git branch --delete --force old",
    "git worktree add ../x", "git -C repo worktree add ../x",
    "bash -c 'git reset --hard'",
    "git reset --hard 'unclosed",
    'echo "$(git reset --hard)"', "eval git push -f", "nice -n 5 git clean -fd",
    "{ git push --force; }", "echo issue#1; git reset --hard",
    "echo x | xargs git reset --hard",
    "git push --mirror", "git push origin :feat/x", "git push origin --delete x", "git push -d origin x",
    "git branch -Df old", "git branch -df old",
]
ALWAYS_ALLOW = [
    "git status", "git push origin feat/x", "git push -u origin feat/x", "git push --follow-tags",
    "git reset HEAD~1", "git clean -n", "git branch -d merged", "git worktree list",
    'git commit -m "docs: explain git reset --hard"', "echo 'git push --force'",
    "git commit -m \"$(cat <<'EOF'\nfix: avoid git reset --hard in docs\nEOF\n)\"",
    "git status # reset --hard", "cd /tmp && git log",
    "find . -exec git add {} \\;",
    "git clean -fdn", "git clean -f --dry-run",
]
IMPLEMENTER_DENY = [
    "git add .", "git commit -m 'feat: x'", "git stash", "git stash push",
    "git checkout .", "git switch main", "git restore x", "git reset HEAD~1",
    "git rebase main", "git merge x", "git cherry-pick abc", "git revert abc",
    "git pull", "git push origin x", "git rm x", "git mv a b", "git apply p.diff",
    "git am p.patch", "git update-ref HEAD abc", "git tag v1", "git branch -f x HEAD",
    "git -c k=v commit -m x", "/usr/bin/git add .", "git --git-dir=.git add .",
    "echo x | xargs git reset --hard", "find . -exec git add {} \\;",
    "git bisect start", "git branch feat/x", "git worktree remove ../x", "git submodule update",
    "git filter-branch", "git config user.name x", "git sparse-checkout set x", "git notes add",
]
IMPLEMENTER_ALLOW = [
    "git status", "git diff", "git log --oneline", "git stash list", "git stash show",
    "git tag", "git tag -l", "git branch", "echo git add",
    "git tag --contains abc", "git branch -a", "git remote -v", "git config --get user.name",
    "git fetch origin", "git rev-parse HEAD", "find ~/git -name x",
]


class Guard(unittest.TestCase):
    def test_always_deny(self):
        for cmd in ALWAYS_DENY:
            self.assertEqual(decision(cmd), "deny", cmd)

    def test_always_allow(self):
        for cmd in ALWAYS_ALLOW:
            self.assertEqual(decision(cmd), "allow", cmd)

    def test_implementer_deny(self):
        for cmd in IMPLEMENTER_DENY:
            self.assertEqual(decision(cmd, implementer=True), "deny", cmd)

    def test_implementer_allow(self):
        for cmd in IMPLEMENTER_ALLOW:
            self.assertEqual(decision(cmd, implementer=True), "allow", cmd)

    def test_bad_json(self):
        self.assertEqual(decision(None, raw="not json"), "allow")
        self.assertEqual(decision(None, implementer=True, raw="not json"), "deny")
