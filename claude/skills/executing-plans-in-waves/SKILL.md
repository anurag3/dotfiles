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
3. Dispatch all `implementer` agents of a wave in one message, so that they run in parallel. Give each agent its task text, its `Files:` list, and the interfaces from earlier tasks. Set the `model` of each agent from [Model selection](#model-selection).
4. After the wave, run the full test suite. Review the wave diff with a reviewer agent that follows `sam-review` (CLAUDE.md rule 11).
5. For each finding, resume the implementer that owns the file (`SendMessage`). If findings remain after a fix round, follow [Model escalation](#model-escalation). Stop after 3 fix rounds for each task and ask the user.
6. Commit each task separately (CLAUDE.md rule 12). Then append `Task <N>: complete (<sha>)` to a `progress.md` file next to the plan.
7. After compaction, read `progress.md` and `git log` before you dispatch. Do not dispatch a task again if it is complete.

## Model selection

Read each task before you dispatch it. Find its difficulty in this table.

| Task difficulty | Agent `model` |
|---|---|
| Mechanical: configuration, documentation, renames, or code that the task text gives in full | `haiku` |
| Standard: a feature or bug fix in one area, with a clear test | `sonnet` |
| Hard: changes across modules, concurrency, security, data migrations, or an unclear design | Do not set `model`. The agent then uses the session model. |

If a task matches more than one row, use the harder row.

### Model escalation

If findings remain after a fix round, and the task used `haiku` or `sonnet`, move the task up one tier:

1. Dispatch a new `implementer` with the next tier. `haiku` changes to `sonnet`. `sonnet` changes to no `model`.
2. Give the new implementer the task text, its `Files:` list, the open findings, and the current diff of its files.
3. Do not reset the round count. The 3-round limit of step 5 counts all fix rounds of the task, before and after escalation.

If the task used no `model`, do not escalate. Continue with step 5.

## Exceptions

- Use a different approach only when the user explicitly asks for inline execution or another approach.
