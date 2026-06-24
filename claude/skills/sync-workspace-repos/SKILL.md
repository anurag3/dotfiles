---
name: sync-workspace-repos
description: >
  Switch all Claude Code workspace repositories to the main branch and pull the latest changes.
  Use whenever the user says "sync repos", "sync workspace", "pull latest", "switch to main",
  "update all repos", "get latest changes", "refresh repos", "update my repos", or any variation
  of wanting to sync, update, or switch multiple repositories in the workspace to their main branch.
  Also trigger when the user is starting work on a new task and mentions wanting fresh code.
---

Switch every git repository in the workspace to main and pull the latest changes.

## Steps

1. Collect all workspace directories from your environment context — the primary working directory plus every additional working directory listed at session start.

2. For each directory, run sequentially:

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
