---
name: handoff
description: >
  Writes a handoff markdown note with completed work, in-progress items and their status-check
  commands, next steps, and auth state to refresh, so a later session can resume. Use when the
  user asks for a handoff note, asks to wrap up, pause, or end the session, or invokes /handoff.
allowed-tools: Bash(git rev-parse *) Bash(git branch *) Bash(git status *) Bash(git log *) Bash(echo *)
---

# Handoff

Author a single markdown file capturing where this session stands, so the next session (yours
or someone else's) can resume without re-discovering what happened.

## Current state

The block below shows the branch, `git status --short`, and `git log --oneline -10`. It shows
"Not a git repository." when the working directory is not in a git repository.

```!
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && { git branch --show-current; git status --short; git log --oneline -10 2>/dev/null || echo "No commits yet."; } || echo "Not a git repository."
```

## Where to write it

Default to `HANDOFF.md` in the current repo's root. If the session was plan-mode work with a
spec/plan directory already in play, default to that directory instead. If neither is obvious,
ask the user where to write it.

## How to gather the content

Derive the draft from actual session state — don't ask the user to dictate it from scratch:

- The git state in "Current state" above. Run git commands only for detail that it does not
  show, for example a diff or commits older than the last 10.
- Commands run this session, especially any still running or left unresolved (a query, a
  rebase, a long job)
- The active todo list, if one exists, for completed vs. outstanding items
- Any auth/session setup done this session (Databricks profile switch, MCP/OAuth connect, env
  vars exported)

Present the draft and let the user confirm or correct it — don't invent details you can't back
with evidence from the above.

## Required sections

Write exactly these four sections, in this order:

1. **Completed** — what was actually finished and verified this session, not just attempted.
2. **In progress / blocked** — anything still running or unresolved. For each item, give the
   *exact command* to check its current status (e.g. `gh pr checks --watch`, `git status`,
   the specific job/query ID and how to poll it) — never a vague "check on X."
3. **Next steps** — up to 3 concrete next actions, ordered.
4. **Auth / environment state to refresh** — anything that may have expired or needs
   re-verification before resuming: Databricks profile validity (`databricks auth profiles`),
   MCP/OAuth connectors, env vars the session relied on.

## Constraints

- Produce one markdown file and stop. No state-tracking mechanism, no database, no background
  process.
- Do not touch auto-memory.
- Do not create a git commit — the user decides whether to commit the handoff file.
