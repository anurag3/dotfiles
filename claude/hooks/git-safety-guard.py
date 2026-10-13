#!/usr/bin/env python3
"""PreToolUse guard for Bash: blocks destructive git commands in all forms.

The deny rules in settings.json match command text only. They miss forms such
as `git -C . reset --hard` and `git push origin +main`. This hook parses each
simple command and checks the git subcommand.

The ask rules in settings.json also match command text only. This hook asks
the user before every other form of `git push`, `gh pr create`, and
`gh pr new`. A deny for one simple command has priority over an ask.

With --implementer, it allows only read-only git commands. Parallel
implementers share one working tree, and the controller commits after each
wave.

Fail policy: on bad input, deny in --implementer mode and allow otherwise. On
a parse error, deny if the command contains "git".
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import cmdparse  # noqa: E402

PUSH_VALUE_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
READ_ONLY = {
    "help", "version", "status", "diff", "log", "show", "blame", "grep", "ls-files", "ls-tree",
    "ls-remote", "rev-parse", "rev-list", "describe", "cat-file", "shortlog", "merge-base",
    "name-rev", "fetch", "for-each-ref", "check-ignore", "show-ref",
}
TAG_LIST_OPTS = {"-l", "--list", "--contains", "--no-contains", "--merged", "--no-merged", "--points-at"}
BRANCH_LIST_OPTS = {"-l", "--list", "-a", "-r", "-v", "-vv", "--contains", "--merged", "--no-merged",
                    "--show-current"}
BRANCH_WRITE_OPTS = {"-f", "--force", "-m", "-M", "--move", "-d", "-D", "--delete", "-c", "-C", "--copy"}
CONFIG_READ_OPTS = {"--get", "--get-all", "--list", "-l", "--get-regexp"}
FIND_EXEC_FLAGS = {"-exec", "-execdir", "-ok", "-okdir"}
IMPLEMENTER_MESSAGE = ("Blocked: implementers must not change git state. The controller commits after the wave. "
                       "Report your changes instead.")


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": reason}}))
    sys.exit(0)


def deny(reason):
    decide("deny", reason)


def short_flag(args, letter):
    return any(re.fullmatch(rf"-[a-zA-Z]*{letter}[a-zA-Z]*", a) for a in args)


def destructive(sub, rest):
    """Return a reason when the git command discards work or rewrites history, else None."""
    if sub == "push":
        refs = cmdparse.positionals(rest, PUSH_VALUE_FLAGS)
        if short_flag(rest, "f") or any(a.startswith("--force") for a in rest) or any(r.startswith("+") for r in refs):
            return "force push"
        if short_flag(rest, "d") or {"--delete", "--mirror"} & set(rest) or any(r.startswith(":") for r in refs):
            return "push --delete or --mirror"
    if sub == "reset" and "--hard" in rest:
        return "reset --hard"
    if (sub == "clean" and (short_flag(rest, "f") or "--force" in rest)
            and not (short_flag(rest, "n") or "--dry-run" in rest)):
        return "clean -f"
    if sub == "branch" and (short_flag(rest, "D") or (
            (short_flag(rest, "d") or "--delete" in rest) and (short_flag(rest, "f") or "--force" in rest))):
        return "force branch delete"
    if sub == "worktree" and cmdparse.positionals(rest, set())[:1] == ["add"]:
        return "worktree add (CLAUDE.md rule 7)"
    return None


def implementer_allowed(sub, rest):
    """Return True only for a git command that cannot change the index, HEAD, refs, config, or the working tree."""
    if sub is None or sub in READ_ONLY:
        return True
    opts, pos = set(rest), cmdparse.positionals(rest, set())
    if sub == "stash":
        return pos[:1] in (["list"], ["show"])
    if sub == "tag":
        return not pos or bool(TAG_LIST_OPTS & opts)
    if sub == "branch":
        return not BRANCH_WRITE_OPTS & opts and (not pos or bool(BRANCH_LIST_OPTS & opts))
    if sub == "remote":
        return pos[:1] in ([], ["show"], ["get-url"])
    if sub == "config":
        return bool(CONFIG_READ_OPTS & opts)
    if sub == "reflog":
        return pos[:1] in ([], ["show"])
    return False


def git_args(argv):
    """Return the args after `git` for a direct or runner call (`xargs git ...`), else None."""
    if argv[0] == "git":
        return argv[1:]
    if argv[0] not in cmdparse.RUNNERS:
        return None
    start = 1
    # A find path can have the basename `git`. Only the command after an exec action runs.
    if argv[0] == "find":
        start = next((i + 1 for i, arg in enumerate(argv) if arg in FIND_EXEC_FLAGS), len(argv))
    for i in range(start, len(argv)):
        if os.path.basename(argv[i]) == "git":
            return argv[i + 1:]
    return None


def main():
    implementer = "--implementer" in sys.argv[1:]
    try:
        command = json.load(sys.stdin)["tool_input"]["command"]
        if not isinstance(command, str):
            raise TypeError("command is not a string")
    except Exception:
        if implementer:
            deny("[BLOCKED] git-safety-guard could not read the hook input.")
        return
    try:
        parsed = cmdparse.simple_commands(command)
    except ValueError:
        if re.search(r"\bgit\b", command):
            deny("[BLOCKED] git-safety-guard could not parse this command. Fix the quoting.")
        return
    ask_reason = None
    for _, argv, _ in parsed:
        if argv[0] == "gh" and cmdparse.split_gh(argv[1:])[:2] in (["pr", "create"], ["pr", "new"]):
            ask_reason = ask_reason or "gh pr create needs user confirmation (settings ask rule)."
        args = git_args(argv)
        if args is None:
            continue
        # The guard cannot know which git command a runner makes, so an implementer cannot use git through a runner.
        if implementer and argv[0] != "git":
            deny(IMPLEMENTER_MESSAGE)
        _, sub, rest = cmdparse.split_git(args)
        reason = destructive(sub, rest)
        if reason:
            deny(f"[BLOCKED] git {reason} discards work or rewrites history. Ask the user to run it with `!`.")
        if implementer and not implementer_allowed(sub, rest):
            deny(IMPLEMENTER_MESSAGE)
        if sub == "push":
            ask_reason = ask_reason or "git push needs user confirmation (settings ask rule)."
    # A later simple command can still deny, so the ask comes only after the full scan.
    if ask_reason:
        decide("ask", ask_reason)


if __name__ == "__main__":
    main()
