# RTK - Rust Token Killer

**Usage**: Token-optimized CLI proxy (60-90% savings on dev operations)

Run `rtk proxy <cmd>` to get raw, unfiltered output when the filtered output hides what you need.

## Hook-Based Usage

`ls`, `grep`, `find`, `git`, `gh`, `read`, `wc`, `tree` are auto-rewritten and
auto-allowed (see `claude/settings.json`). Other rtk subcommands (docker,
kubectl, aws, pnpm, psql, dotnet, ...) are still rewritten by the hook but
will prompt for permission unless added to the allow list.
