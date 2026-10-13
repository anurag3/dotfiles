# `permissions` reference

This file explains each rule in the `permissions` block of `settings.json`. JSON cannot hold comments, so the explanations are in this file.

The built-in read-only commands (`ls`, `cat`, `grep`, `find`, `wc`, `pwd`, `cd`) need no rule.

## `allow`

Claude runs these commands without a prompt.

| Rule | What it allows |
|---|---|
| `Bash(tree *)` | Print a directory tree |
| `Bash(git *)` | Run a `git` subcommand |
| `Bash(gh *)` | Run a GitHub CLI (`gh`) subcommand |
| `Bash(sbt *)` | Run an `sbt` (Scala build tool) subcommand |
| `Bash(mkdir -p ~/.claude/plans/**)` | Make plan directories through the `~` path |
| `Bash(mkdir -p /Users/anurag.desai/.claude/plans/**)` | Make plan directories through the absolute path |
| `Bash(mkdir -p ~/.claude/specs/**)` | Make spec directories through the `~` path |
| `Bash(mkdir -p /Users/anurag.desai/.claude/specs/**)` | Make spec directories through the absolute path |
| `Edit(~/.claude/plans/**)` | Write and edit files in the plans directory |
| `Edit(~/.claude/specs/**)` | Write and edit files in the specs directory |
| `Bash(defaults read *)` | Read macOS preferences with `defaults read` |

## `ask`

Claude asks for approval before it runs these commands. An `ask` rule has priority over the `Bash(git *)` and `Bash(gh *)` allow rules.

| Rule | Why it asks |
|---|---|
| `Bash(git push *)` | Approve each push to a remote branch |
| `Bash(gh pr create *)` | Approve each new pull request |

## `deny`

Claude cannot run these commands.

| Rule | What it blocks |
|---|---|
| `Bash(git push --force *)` | Force push |
| `Bash(git push -f *)` | Force push (short flag) |
| `Bash(git reset --hard *)` | Hard reset that removes local changes |
| `Bash(git clean -f *)` | Removal of untracked files |
| `Bash(git branch -D *)` | Forced removal of a branch |
| `Bash(gh pr merge *)` | Pull request merge |
| `Bash(gh repo delete *)` | Repository removal |
| `Bash(git worktree add *)` | New git worktree (CLAUDE.md rule 7) |
| `EnterWorktree` | The worktree tool (CLAUDE.md rule 7) |

A deny rule matches the command text only. The `git-safety-guard.py` hook also blocks the forms that text matching misses, for example `git -C . reset --hard` and `git push origin +main`.

## Other keys

| Key | Value | What it does |
|---|---|---|
| `defaultMode` | `auto` | Start each session in auto mode |
| `additionalDirectories` | `~/.claude/plans/`, `~/.claude/specs/` | Give Claude access to the plans and specs directories from all projects |
