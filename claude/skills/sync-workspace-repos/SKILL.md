---
name: sync-workspace-repos
description: >
  Switches every Claude Code workspace repository to its main (or master) branch, pulls the
  latest changes, and reports each repo it cannot sync. Invoke with /sync-workspace-repos.
disable-model-invocation: true
context: fork
agent: general-purpose
model: haiku
background: false
---

Switch every git repository in the workspace to main and pull the latest changes.

## Steps

1. Collect the workspace directories from the environment section of your own system prompt:
   - The primary working directory.
   - Each additional working directory.

   If you see only one directory, state this in the summary.

2. For each directory, run sequentially:

   Before the checkout, make sure that the directory is a git repository:
   ```
   git -C <dir> rev-parse --is-inside-work-tree
   ```

   If this command fails, do not sync the directory. In the summary, list it as "skipped: not a git repo", not as a failure.

   First, try checking out main; fall back to master if main doesn't exist:
   ```
   git -C <dir> checkout main 2>/dev/null || git -C <dir> checkout master
   ```

   Then pull:
   ```
   git -C <dir> pull
   ```

3. After all repos are done, print a summary — one line per repo with: the directory name, which branch it landed on, and pull result. Flag any failures clearly.

## Important constraints

- Never force or stash. If checkout fails due to uncommitted changes or conflicts, report it and skip the pull for that repo.
- Run repos one at a time so output is easy to read.
- Don't discard local work — just report what blocked the sync.
