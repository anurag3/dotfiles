#!/usr/bin/env python3
"""PreToolUse guard for Bash: enforces global CLAUDE.md rules 12 (Conventional
Commits) and 13 (no attribution or internal artifacts in commits and PRs).

Checks, with or without a leading `rtk`:
  - `git commit` with `-m`, `-F <file>`, `-F -` (heredoc), and `--trailer`:
    Conventional Commit subject, no banned text.
  - `git checkout -b/-B`, `git switch -c/-C/--create`, `git branch <name>`,
    `git branch -m/-M`: branch name `<type>/<kebab>`.
  - `gh pr create` and `gh pr edit` with `--title`, `--body`, `--body-file`:
    same subject format, no banned text.

Fails open: if the hook input, the command, or a message file cannot be read,
it allows.
"""
import json
import os
import re
import shlex
import sys

TYPES = "feat|fix|chore|docs|refactor|test|perf|ci|build"
SUBJECT = re.compile(rf"^({TYPES})(\([A-Za-z0-9._/-]+\))?!?: \S")
BRANCH = re.compile(rf"^({TYPES})/[a-z0-9][a-z0-9-]*$")
BANNED = re.compile(
    r"generated with \[?claude|co-authored-by:\s*claude|noreply@anthropic\.com"
    r"|\.claude/plans|\.claude/specs|fix round|per the plan|ponytail"
    r"|^[ \t]*(?:[-*][ \t]+)?\(?task \d+\b",
    re.I | re.M,
)
# `"$(cat <<'EOF' ... EOF\n)"`: the body becomes one argument value.
CAT_HEREDOC = re.compile(
    r"\$\(\s*cat\s+<<-?\s*(['\"]?)(\w+)\1[ \t]*\n(.*?)\n[ \t]*\2[ \t]*\n?\s*\)", re.S
)
# Any other heredoc: the body becomes the stdin of its command, never command text.
HEREDOC = re.compile(r"(?<!<)<<-?[ \t]*(['\"]?)(\w+)\1([^\n]*)\n(.*?)\n[ \t]*\2[ \t]*(?=\n|$)", re.S)
SEPARATOR = re.compile(r"^[;&|()\n]+$")
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
BRANCH_CREATE_OPTS = {"-f", "--force", "-t", "--track", "--no-track", "-q", "--quiet"}
BRANCH_RENAME_OPTS = {"-m", "-M", "--move"}

SUBJECT_HELP = (
    f"Expected `<type>: <description>` or `<type>(<scope>): <description>`, "
    f"where <type> is one of {TYPES.replace('|', ', ')}."
)
BANNED_HELP = (
    "Remove AI attribution, plan/spec paths, task or fix-round bookkeeping, "
    "and skill names. State only what the change does."
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


def segments(command: str) -> list:
    """Split a shell command into (tokens, heredoc stdin) for each simple command."""
    stash = []

    def keep(text: str, kind: str) -> str:
        stash.append(text)
        return f"__{kind}{len(stash) - 1}__"

    command = CAT_HEREDOC.sub(lambda m: keep(m.group(3), "ARG"), command)
    command = HEREDOC.sub(lambda m: f" {keep(m.group(4), 'STDIN')} {m.group(3)}", command)

    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    result, tokens, stdin = [], [], None
    for tok in lex:
        placeholder = re.fullmatch(r"__(ARG|STDIN)(\d+)__", tok)
        if SEPARATOR.match(tok):
            result.append((tokens, stdin))
            tokens, stdin = [], None
        elif placeholder and placeholder.group(1) == "STDIN":
            stdin = stash[int(placeholder.group(2))]
        else:
            tokens.append(stash[int(placeholder.group(2))] if placeholder else tok)
    result.append((tokens, stdin))
    return [(t, s) for t, s in result if t]


def strip_prefix(tokens: list) -> list:
    """Drop env assignments and a leading `rtk`."""
    i = 0
    while i < len(tokens) and re.match(r"^\w+=", tokens[i]):
        i += 1
    if i < len(tokens) and tokens[i] == "rtk":
        i += 1
    return tokens[i:]


def option_values(args: list, short: str, long: str) -> list:
    """Collect values for `-x V`, `-xV`, `-abx V`, `--long V`, `--long=V`."""
    values, i = [], 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            break
        if long and arg == long:
            values.append(args[i + 1] if i + 1 < len(args) else "")
            i += 2
            continue
        if long and arg.startswith(long + "="):
            values.append(arg[len(long) + 1:])
        elif short and re.match(rf"^-[a-zA-Z]*{short}", arg) and not arg.startswith("--"):
            rest = arg[arg.index(short) + 1:]
            if rest:
                values.append(rest)
            else:
                values.append(args[i + 1] if i + 1 < len(args) else "")
                i += 1
        i += 1
    return values


def read_text(path: str, stdin, base: str):
    """Return the text of a message file, `-` for heredoc stdin, or None if unreadable."""
    if path == "-":
        return stdin
    try:
        with open(os.path.join(base, os.path.expanduser(path))) as handle:
            return handle.read()
    except OSError:
        return None


def valid_subject(subject: str) -> bool:
    prefixed = re.match(r'^(?:(?:fixup|squash|amend)! (.*)|Revert "(.*)")$', subject)
    if prefixed:
        return valid_subject(prefixed.group(1) or prefixed.group(2) or "")
    return bool(SUBJECT.match(subject))


def check_subject(subject: str, what: str) -> None:
    # A `$VAR` or `$(...)` value is expanded by the shell, so the hook cannot see it.
    if not subject.startswith("$") and not valid_subject(subject):
        deny(f"[BLOCKED] CLAUDE.md rule 12: {what} `{subject}` is not a Conventional "
             f"Commit subject. {SUBJECT_HELP}")


def check_banned(text: str, what: str) -> None:
    match = BANNED.search(text)
    if match:
        deny(f"[BLOCKED] CLAUDE.md rule 13 (skill names: rule 12): {what} contains "
             f"`{match.group(0).strip()}`. {BANNED_HELP}")


def check_message(message, what: str) -> None:
    if message and message.strip():
        check_subject(message.strip().splitlines()[0], f"{what} subject")
        check_banned(message, what)


def check_branch(name: str) -> None:
    if not BRANCH.match(name) or "ponytail" in name:
        deny(f"[BLOCKED] CLAUDE.md rule 12: branch name `{name}` must be `<type>/<description>` "
             f"in kebab-case (e.g. `fix/null-check-in-foo`), with no skill name. "
             f"<type> is one of {TYPES.replace('|', ', ')}.")


def check_git(args: list, stdin, base: str) -> None:
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            base = os.path.join(base, args[i + 1])
        i += 2 if args[i] in GIT_OPTS_WITH_VALUE else 1
    if i >= len(args):
        return
    sub, rest = args[i], args[i + 1:]

    if sub == "commit":
        messages = option_values(rest, "m", "--message")
        if messages:
            check_message("\n\n".join(messages), "commit message")
        else:
            for path in option_values(rest, "F", "--file")[:1]:
                check_message(read_text(path, stdin, base), "commit message")
        for trailer in option_values(rest, "", "--trailer"):
            check_banned(trailer, "commit trailer")
    elif sub == "checkout":
        for name in option_values(rest, "b", "") + option_values(rest, "B", ""):
            check_branch(name)
    elif sub == "switch":
        for name in option_values(rest, "c", "--create") + option_values(rest, "C", "--force-create"):
            check_branch(name)
    elif sub == "branch":
        options = [a for a in rest if a.startswith("-")]
        names = [a for a in rest if not a.startswith("-")]
        if any(o in BRANCH_RENAME_OPTS for o in options):
            if names:
                check_branch(names[-1])
        elif names and all(o.split("=")[0] in BRANCH_CREATE_OPTS for o in options):
            check_branch(names[0])


def check_gh(args: list, stdin, base: str) -> None:
    if len(args) < 2 or args[0] != "pr" or args[1] not in ("create", "edit"):
        return
    rest = args[2:]
    for title in option_values(rest, "t", "--title"):
        check_subject(title, "PR title")
        check_banned(title, "PR title")
    for body in option_values(rest, "b", "--body"):
        check_banned(body, "PR body")
    for path in option_values(rest, "F", "--body-file"):
        check_banned(read_text(path, stdin, base) or "", "PR body file")


def main() -> None:
    try:
        data = json.load(sys.stdin)
        if data.get("tool_name") != "Bash":
            return
        command = data.get("tool_input", {}).get("command", "")
        cwd = data.get("cwd") or os.getcwd()
    except Exception:
        return
    if not command:
        return

    try:
        parsed = segments(command)
    except ValueError:
        return

    for tokens, stdin in parsed:
        tokens = strip_prefix(tokens)
        if not tokens:
            continue
        if tokens[0] == "git":
            check_git(tokens[1:], stdin, cwd)
        elif tokens[0] == "gh":
            check_gh(tokens[1:], stdin, cwd)


if __name__ == "__main__":
    main()
