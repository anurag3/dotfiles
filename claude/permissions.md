# `permissions.allow` reference

Documents what each rule in `settings.json`'s `permissions.allow` list does. Kept as a
separate file because `settings.json` is strict JSON and can't hold inline comments.

| Rule | What it allows |
|---|---|
| `Bash(ls *)` | List directory contents |
| `Bash(cd *)` | Change the shell's working directory |
| `Bash(pwd *)` | Print the current working directory |
| `Bash(cat *)` | Print file contents |
| `Bash(grep *)` | Search file contents for a pattern |
| `Bash(find *)` | Search the filesystem for files/directories |
| `Bash(read *)` | Bash builtin for reading input/variables |
| `Bash(wc *)` | Count lines/words/bytes in input |
| `Bash(tree *)` | Print a directory tree |
| `Bash(git *)` | Run any `git` subcommand |
| `Bash(gh *)` | Run any GitHub CLI (`gh`) subcommand |
| `Bash(sbt *)` | Run any `sbt` (Scala build tool) subcommand |
| `Bash(rtk ls *)` | `ls` proxied through `rtk` (token-optimized CLI) |
| `Bash(rtk grep *)` | `grep` proxied through `rtk` |
| `Bash(rtk find *)` | `find` proxied through `rtk` |
| `Bash(rtk git *)` | `git` proxied through `rtk` |
| `Bash(rtk gh *)` | `gh` proxied through `rtk` |
| `Bash(rtk read *)` | `read` proxied through `rtk` |
| `Bash(rtk wc *)` | `wc` proxied through `rtk` |
| `Bash(rtk tree *)` | `tree` proxied through `rtk` |
| `Bash(sbt test *)` | Explicit `sbt test` variants (redundant with `sbt *`, kept for clarity) |
| `Bash(mkdir -p /Users/anurag.desai/.claude/plans/**)` | Create plan directories under the absolute plans path |
| `Bash(mkdir -p ~/.claude/plans/**)` | Create plan directories under the `~`-relative plans path |
| `Bash(rtk mkdir -p /Users/anurag.desai/.claude/plans/**)` | Same as above, proxied through `rtk` |
| `Bash(rtk mkdir -p ~/.claude/plans/**)` | Same as above, proxied through `rtk` |
| `Write(/Users/anurag.desai/.claude/plans/**)` | Create/overwrite files under the absolute plans path |
| `Write(~/.claude/plans/**)` | Create/overwrite files under the `~`-relative plans path |
| `Edit(/Users/anurag.desai/.claude/plans/**)` | Edit existing files under the absolute plans path |
| `Edit(~/.claude/plans/**)` | Edit existing files under the `~`-relative plans path |
| `Bash(defaults read *)` | Read macOS app/system preferences via `defaults read` |
