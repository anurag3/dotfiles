---
name: handoff
description: >
  Write a handoff note summarizing the current session's state before pausing or ending it.
  Use when the user asks for a handoff note, asks to wrap up/pause/end the session, or
  explicitly invokes /handoff.
---

# Handoff

Author a single markdown file capturing where this session stands, so the next session (yours
or someone else's) can resume without re-discovering what happened. This is the authoring
counterpart to `session-resume` — that skill recovers from a crashed session's JSONL; this one
writes the note in the first place. Don't duplicate its recovery logic here.

## Where to write it

Default to `HANDOFF.md` in the current repo's root. If the session was plan-mode work with a
spec/plan directory already in play, default to that directory instead. If neither is obvious,
ask the user where to write it.

## How to gather the content

Derive the draft from actual session state — don't ask the user to dictate it from scratch:

- `git status` and `git log` (recent commits, uncommitted/staged changes, current branch)
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
- Do not attempt to automate resumption; that's `session-resume`'s job, not this skill's.
