---
name: executing-plans-in-waves
description: >
  Executes a multi-task implementation plan in parallel waves of implementer subagents, with a
  sam-review reviewer pass, per-task commits, and a progress.md ledger. Use when executing any plan
  that has Files: and Depends on: lines per task, or when resuming plan execution after compaction.
---

# Executing Plans in Waves

Each plan task has a `Files:` list and a `Depends on:` line (CLAUDE.md rule 5).

## Procedure

1. Put the tasks into waves. A wave contains tasks whose dependencies are complete and whose `Files:` lists do not overlap.
2. If two ready tasks share a file, put them in different waves.
3. Dispatch all `implementer` agents of a wave in one message, so that they run in parallel. Give each agent its task text, its `Files:` list, and the interfaces from earlier tasks.
4. After the wave, run the full test suite. Review the wave diff with a reviewer agent that follows `sam-review` (CLAUDE.md rule 11).
5. For each finding, resume the implementer that owns the file (`SendMessage`). Stop after 3 fix rounds for each task and ask the user.
6. Commit each task separately (CLAUDE.md rule 12). Then append `Task <N>: complete (<sha>)` to a `progress.md` file next to the plan.
7. After compaction, read `progress.md` and `git log` before you dispatch. Do not dispatch a task again if it is complete.

## Exceptions

- Use a different approach only when the user explicitly asks for inline execution or another approach.
