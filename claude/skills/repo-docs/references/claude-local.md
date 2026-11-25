# CLAUDE.local.md managed block

`CLAUDE.local.md` is at the repo root. Claude Code loads it in each session in the repo, so each line costs context. The skill owns one block in the file. The user owns the rest.

## Budget

- The full file: about 80 lines or fewer.
- The managed block: 50 lines or fewer, markers included.
- If the block is too long, cut the lowest-value gotchas and routing rows first. The full lists stay in `.docs/`.

## Block template

The rows below are illustrative. Use facts from the repo's own `.docs/`.

```markdown
<!-- repo-docs:begin -->
## Local notes (managed by repo-docs)

Start at `.docs/README.md`. Read only the note for your task area.

### Corrections to repo docs

| Repo doc says | Correct value | Evidence |
|---|---|---|
| `README.md:40`: the job runs hourly | Airflow starts the job each night. `databricks.yml:52` has no schedule | `dags/load.py:18` |

### Top gotchas

- `loader/sample.py:14` samples with `LIMIT` and no `ORDER BY`. Joins between sampled tables mostly miss.
- More: [.docs/gotchas.md](.docs/gotchas.md).

### Top confirmed bugs

- `loader/merge.py:88`: the INSERT swaps `external_id` and `external_source`.
- Full list: [.docs/known-issues.md](.docs/known-issues.md).

### Where to read

| Task area | Read |
|---|---|
| Job definitions, deploy, containment | `.docs/code-flow.md` |
| Sources, tables, sinks | `.docs/data-flow.md` |
| Loader merge logic | `.docs/loader.md` |
<!-- repo-docs:end -->
```

## Section rules

1. **Corrections to repo docs.** Each row is a statement in `README.md`, `AGENTS.md`, or `CLAUDE.md` that the code contradicts. These rows have the highest value, because the wrong text loads in each session. Copy each row from the "Doc drift" section of `known-issues.md`.
2. **Top gotchas.** A maximum of 8 lines, from `gotchas.md`. Select the gotchas that cause silent wrong results or a damaged live system. End with the link to `gotchas.md`.
3. **Top confirmed bugs.** A maximum of 3 lines, from the "Confirmed bugs" section of `known-issues.md`. End with the link to `known-issues.md`.
4. **Where to read.** One row for each task area. Each row names one `.docs/` file. Use the task words that a user types, not the file names.
5. Each line in the block is a copy of a fact in `.docs/`. Do not add a fact that is only in the block. When `.docs/` changes, update the block from it.
6. Omit a section that has no content.

## Rules for an existing file

1. Keep the text outside the markers exactly as it is. Do not reformat it, move it, or correct it.
2. If the file has no block, add the block at the end of the file.
3. If the file has no markers but has content that `.docs/` also holds (bug lists, gotchas, routing tables), do these steps during the first `audit`:
   1. Show the user the duplicated lines and the proposed block.
   2. Wait for approval.
   3. Move the approved lines into the block or into `.docs/`. Delete only the lines that the user approved.
4. If the user content contradicts `.docs/`, do not change the user content. Report the conflict to the user.
5. If the file does not exist, create it with one H1 (`# CLAUDE.local.md`), one line that says git ignores the file, and the block.

## Before you write

Make sure that git ignores the file: `git check-ignore -q CLAUDE.local.md`. If the command fails, stop and tell the user. A tracked `CLAUDE.local.md` would put local notes in a commit.
