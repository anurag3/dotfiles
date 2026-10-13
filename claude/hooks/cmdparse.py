"""Shared shell-command parser for the PreToolUse Bash guards.

The guards check argv[0] of each simple command, not the raw command text.
A quoted mention of a command then causes no block. A chain, a wrapper, or
`bash -c` then causes no bypass.

The parser also reads into `$(...)`, backticks, `eval`, `bash -c`, and a
heredoc that goes to a shell. A guard can over-detect, because a single-quoted
`$(...)` is also read as a command.

Known limitation: the parser cannot read a script that goes into a bare shell
from a pipe or a here-string, for example `echo 'x' | bash` or `bash <<< 'x'`.
"""
import os
import re
import shlex

# `"$(cat <<'EOF' ... EOF\n)"`: the body becomes one argument value.
CAT_HEREDOC = re.compile(
    r"\$\(\s*cat\s+<<-?\s*(['\"]?)(\w+)\1[ \t]*\n(.*?)\n[ \t]*\2[ \t]*\n?\s*\)", re.S
)
# Any other heredoc: the body becomes the stdin of its command, never command text.
HEREDOC = re.compile(r"(?<!<)<<-?[ \t]*(['\"]?)(\w+)\1([^\n]*)\n(.*?)\n[ \t]*\2[ \t]*(?=\n|$)", re.S)
SEPARATOR = re.compile(r"^[;&|()\n]+$")
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
# Wrapper options that take the next token as their value.
WRAPPER_VALUE_FLAGS = {
    "env": {"-u", "--unset", "-C", "--chdir", "-P"},
    "nice": {"-n", "--adjustment"},
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "-T", "--user", "--group", "--chdir"},
    "doas": {"-u", "-C"},
    "time": {"-f", "-o", "--format", "--output"},
    "caffeinate": {"-t", "-w"},
    "exec": {"-a"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
}
WRAPPERS = set(WRAPPER_VALUE_FLAGS) | {"command", "builtin", "nohup", "stdbuf"}
KEYWORDS = {"{", "}", "!", "if", "then", "elif", "else", "fi", "while", "until", "do", "done", "coproc"}
# The guards deny these when a trigger word is in their arguments. The parser does not read into them.
RUNNERS = {"xargs", "find", "watch", "parallel"}
SHELLS = {"sh", "bash", "zsh"}
GH_OPTS_WITH_VALUE = {"-R", "--repo", "--hostname"}
MAX_DEPTH = 3


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
    # A `#` inside a word (`issue#1`) is not a comment. Without this, shlex drops the rest of the line.
    lex.commenters = ""
    result, tokens, stdin = [], [], None
    for tok in lex:
        placeholder = re.fullmatch(r"__(ARG|STDIN)(\d+)__", tok)
        # A quoted `'<<X'` makes a placeholder inside a word. Then the heredoc match is false
        # and it can hide commands as stdin.
        if placeholder and int(placeholder.group(2)) >= len(stash) or (
                not placeholder and re.search(r"__(ARG|STDIN)", tok)):
            raise ValueError("heredoc marker is not a full word")
        if SEPARATOR.match(tok):
            result.append((tokens, stdin))
            tokens, stdin = [], None
        elif placeholder and placeholder.group(1) == "STDIN":
            stdin = stash[int(placeholder.group(2))]
        else:
            tokens.append(stash[int(placeholder.group(2))] if placeholder else tok)
    result.append((tokens, stdin))
    return [(t, s) for t, s in result if t]


def strip_prefix(tokens):
    """Return (env assignments, argv) without wrappers and keywords. argv[0] becomes its basename."""
    env, i = {}, 0
    while i < len(tokens):
        assign = re.match(r"^(\w+)=(.*)$", tokens[i], re.S)
        wrapper = os.path.basename(tokens[i])
        if assign:
            env[assign.group(1)] = assign.group(2)
            i += 1
        elif tokens[i] in KEYWORDS:
            i += 1
        elif wrapper in WRAPPERS:
            value_flags = WRAPPER_VALUE_FLAGS.get(wrapper, set())
            i += 1
            while i < len(tokens) and tokens[i].startswith("-"):
                if wrapper == "env" and tokens[i] in ("-S", "--split-string") and i + 1 < len(tokens):
                    tokens = tokens[:i] + shlex.split(tokens[i + 1]) + tokens[i + 2:]
                else:
                    i += 2 if tokens[i] in value_flags else 1
            # `timeout` takes a duration before the command.
            if wrapper == "timeout":
                i += 1
        else:
            break
    argv = tokens[i:]
    return env, ([os.path.basename(argv[0])] + argv[1:]) if argv else []


def shell_script(argv):
    """Return the script after `-c` (also `-lc`, `-ec`, `-c --`), or None."""
    for i, arg in enumerate(argv[1:], start=1):
        if re.fullmatch(r"-[a-z]*c[a-z]*", arg) and i + 1 < len(argv):
            i += 2 if argv[i + 1] == "--" else 1
            return argv[i] if i < len(argv) else None
    return None


def without_literal_heredocs(command):
    """Remove heredoc bodies with a quoted delimiter. The shell does not expand `$(...)` in them."""
    command = CAT_HEREDOC.sub(lambda m: "" if m.group(1) else m.group(0), command)
    return HEREDOC.sub(lambda m: m.group(3) if m.group(1) else m.group(0), command)


def backtick_bodies(text):
    """Return the body of each backtick span. A backslash before a backtick makes it a literal."""
    bodies, start, i = [], None, 0
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            if start is None:
                start = i + 1
            else:
                bodies.append(text[start:i])
                start = None
        i += 1
    return bodies


def substitutions(text):
    """Return the body of each `$(...)` and each backtick span in text."""
    bodies = backtick_bodies(text)
    start = text.find("$(")
    while start != -1:
        depth, end = 1, start + 2
        while end < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[end], 0)
            end += 1
        if depth == 0:
            bodies.append(text[start + 2:end - 1])
        start = text.find("$(", end if depth == 0 else start + 2)
    return bodies


def simple_commands(command, depth=0):
    """Return (env, argv, heredoc stdin) for each simple command.

    Raise ValueError on bad quoting or on nesting deeper than MAX_DEPTH.
    """
    if depth > MAX_DEPTH:
        raise ValueError("command nesting is too deep")
    out = []
    for tokens, stdin in segments(command):
        env, argv = strip_prefix(tokens)
        if not argv:
            continue
        script = None
        if argv[0] in SHELLS:
            script = shell_script(argv)
            if script is None:
                script = stdin
        elif argv[0] == "eval":
            script = " ".join(argv[1:])
        if script is not None:
            out.extend(simple_commands(script, depth + 1))
        else:
            out.append((env, argv, stdin))
    for body in substitutions(without_literal_heredocs(command)):
        out.extend(simple_commands(body, depth + 1))
    return out


def positionals(args, value_flags):
    """Return non-option args. Skip the value after each flag in value_flags."""
    out, i = [], 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            out.extend(args[i + 1:])
            break
        if arg.startswith("-") and len(arg) > 1:
            i += 2 if arg in value_flags else 1
            continue
        out.append(arg)
        i += 1
    return out


def split_git(args):
    """Return (-C dirs, subcommand, rest) after git global options."""
    dirs, i = [], 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            dirs.append(args[i + 1])
        i += 2 if args[i] in GIT_OPTS_WITH_VALUE else 1
    if i >= len(args):
        return dirs, None, []
    return dirs, args[i], args[i + 1:]


def split_gh(args):
    """Drop leading gh global options."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in GH_OPTS_WITH_VALUE else 1
    return args[i:]
