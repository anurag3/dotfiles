---
name: repo-docs
description: >
  Use when a user asks to create, update, audit, or add to a repo's local `.docs/`
  notes or `CLAUDE.local.md`, for example "generate docs for this repo", "update .docs",
  "docs are stale", or /repo-docs init, update, capture, or audit. Also use when the
  docs-capture-nudge Stop hook asks for `/repo-docs capture`, or when a session finds a
  durable, non-obvious fact about a repo that belongs in local notes (CLAUDE.md rule 15).
---

# repo-docs

## Overview

`.docs/` holds local notes about one repo. Git ignores the folder. The notes are for future Claude sessions: facts that the code and the repo docs do not show, each with a `path:line` citation. `ONE-PAGER.md` is the only file for human readers.

Freshness state is in `.docs/manifest.json`. Only `scripts/docs_state.py` writes its `sha`, `checked`, `branch`, and `generated` fields. Run it as:

```sh
S=~/.claude/skills/repo-docs/scripts/docs_state.py
python3 $S status <repo> [--stale-days N] [--committed]
python3 $S diff <repo> <note>              # diff of the note's covers, note sha to working tree, plus untracked matches
python3 $S stamp <repo> [note ...]         # record HEAD for these notes. No names: all notes, README, top-level sha
python3 $S init-manifest <repo> [--force]  # new manifest. Sets each note's `checked` from its file date, so `status` shows changes since the note was written
```

`status` prints these groups:

- "Affected notes" and "Uncovered changes": committed changes from the base SHA to `HEAD`.
- "Uncommitted changes (not stamped)": working-tree changes, each with its note or "no note". `--committed` omits this group.
- "Broken citations": deleted or renamed paths, and line numbers past the end of the file.
- "Stale time-bound statements" and "Bad dates".

`<repo>` is the git root. `<note>` is a path relative to `.docs/`, for example `gotchas.md`. A missing manifest makes `status`, `diff`, and `stamp` exit with code 2.

You edit only these manifest parts by hand: each note's `covers` list, new note entries (`{"covers": [...]}`), and `"frozen": true` for `investigations/` notes. `references/layout.md` gives the glob rules.

## Mode selection

Use the argument when the user gives one. Otherwise, infer the mode:

| Condition | Mode |
|---|---|
| No `.docs/` folder | `init` |
| `.docs/` exists, no `manifest.json` | `audit` |
| User asks to refresh, or the repo has new commits since the last stamp | `update` |
| One new fact from this session, or the Stop hook asked for capture | `capture` |

If the user asks for `capture` and no `.docs/` exists, ask the user: run `init` now, or skip. If `.docs/` exists but has no manifest, do the capture and then recommend `/repo-docs audit`.

## Contract

Every run obeys these rules.

1. **Freshness.** Freshness data lives only in `manifest.json` and in the `` Checked DATE against `branch` (`sha`). `` line that `stamp` writes under each H1 (`Checked <date> (not a git repo).` outside git). Do not write this line yourself.
2. **Layout.** Use the file names in `references/layout.md`. The only allowed subfolder is `investigations/`.
3. **Markers.** Use exactly two marker words, in prefix form: `Confirmed:` and `Inferred:`. `Confirmed:` means you checked it in source code, a test, or a run. A bug that you read in the code and traced is `Confirmed:`. `Inferred:` means you concluded it but did not check it.
4. **One home for each fact type.** Bugs go only in `known-issues.md`. Gotchas go only in `gotchas.md`. Other files link to them.
5. **Ask before destructive changes.** Before you move, merge, rename, or delete an existing `.docs/` file, show the full list of changes to the user. Wait for approval.
6. **No person names in file names.** Questions for a person go in `open-questions.md`, with the person's name in the line.
7. **Local only.** Do not edit tracked repo files. Do not commit `.docs/` content or paths. Do not run commands against live systems (Databricks, dbt against a warehouse, Airflow, network calls) without the user's approval (CLAUDE.md rules 9, 13, 15).
8. **CLAUDE.local.md.** Update it in each `init`, `update`, and `audit` run. Change only the text between `<!-- repo-docs:begin -->` and `<!-- repo-docs:end -->`. `references/claude-local.md` gives the template and budget.
9. **Time-bound text.** Write each time-bound statement (open PR, rollout status, row count) with `as of YYYY-MM-DD`. `status` finds old ones only with this date format.

Never:

- Add YAML front matter, `verified-at:` lines, or other metadata headers to a note.
- Add scripts or tools to `.docs/`. The state script is the only tool.
- Create `latent-bugs.md`, `bugs.md`, `one-pager.md`, `architecture.md`, or other names outside the layout.
- Use `Verified`, `Probable`, `Read`, or `(inferred)` as markers.
- Put a new fact in a catch-all file such as `domain-notes.md` or `misc.md`.

## Before any mode

Do these steps first in each mode:

1. Invoke the `simplified-technical-english` skill before you write a note (CLAUDE.md rule 8).
2. Find the git root: `git rev-parse --show-toplevel`. If the command fails, do the non-git steps below.
3. Make sure that git ignores the local files. Run `git -C <root> check-ignore -q .docs/README.md` and `git -C <root> check-ignore -q CLAUDE.local.md`. If one of them fails, stop and tell the user.
4. Read `<root>/.docs/README.md` and `<root>/CLAUDE.local.md`, if they exist.
5. Read the repo's `CLAUDE.md`, `AGENTS.md`, and `README.md`. Do not restate them in notes. Link to them.
6. In `audit` and `update`, back up the notes before you change a file. Tell the user the backup path.

   ```sh
   B=~/.claude/backups/repo-docs/$(basename <root>)/$(date +%Y%m%d-%H%M%S) && mkdir -p "$B" && cp -R <root>/.docs "$B/"
   [ -f <root>/CLAUDE.local.md ] && cp <root>/CLAUDE.local.md "$B/"
   ```

If the folder is not a git repo:

1. Use the folder as `<root>`. Skip the `check-ignore` step. Tell the user that the folder is not a git repo.
2. Use `status` to list files changed since the manifest `generated` date.
3. Do not use `diff`. Read the covered files to check each note.
4. Use `stamp` as usual. It records dates only: `Checked <date> (not a git repo).`
5. Skip every step that runs `git`.

## init

1. Map the repo: build files, CI workflows, entry points, job and DAG definitions, and the repo docs.
2. Read `references/layout.md`.
3. Propose the topic list to the user: the core files plus one `<topic>.md` for each component or flow. Wait for approval.
4. If the repo has more than about 50 source files, dispatch one general-purpose subagent for each approved area. Do not use Explore subagents for this, because they only find code. In each brief, do these:
   1. Ask for facts with `path:line`, failure modes, gotchas, and bug candidates.
   2. Paste the checklist and the evidence bar from `references/bug-hunting.md`.
   3. Ask the agent to mark each claim `Confirmed:` or `Inferred:` and to return text only, with no file writes.
5. Check each bug candidate in the source yourself before you mark it `Confirmed:`.
6. Write the core files and the topic files with the templates in `references/layout.md`.
7. Read `references/one-pager.md`. Write `ONE-PAGER.md`.
8. Run `python3 $S init-manifest <root>`.
9. Fill `covers` for each note in `manifest.json`. Leave `README.md` covers empty.
10. Read `references/claude-local.md`. Write the `CLAUDE.local.md` block.
11. Run `python3 $S stamp <root>`.
12. Do the finish checklist.

## update

Update records committed changes only. `stamp` records `HEAD`, so it does not include uncommitted changes. If the user wants notes about uncommitted work, use `capture`.

1. Run `python3 $S status <root>`. Treat the "Uncommitted changes (not stamped)" group as information only.
2. For each note under "Affected notes", do these steps:
   1. Run `python3 $S diff <root> <note>`. The output also includes uncommitted changes.
   2. Check each claim in the note against the committed code. If a covered file has uncommitted changes, read it with `git show HEAD:<path>`. Fix line numbers and wrong facts.
   3. Add new facts from the diff, with `path:line` and a marker.
3. For each bug in `known-issues.md` that a commit fixed, move it to "Resolved". Add the fixing SHA from `git log --oneline <old-sha>..HEAD -- <path>`.
4. For each path under "Uncovered changes", add the path to the `covers` of the correct note. If no note fits, propose a new topic note to the user. Add each new note to `manifest.json` and to the README index.
5. Fix each line under "Broken citations", including lines from before this run. Find the new path with `git log --follow --name-status -- <old-path>`. For a path in another repo, add the repo name as a prefix (`ops-delivery/terraform/role.tf:153`), so the script skips it. Replace an abbreviated path (`MS/Main.scala:62`) with the full repo-relative path.
6. For each line under "Stale time-bound statements", check the fact again. Write the new state with a new `as of` date, or remove the line. Correct each line under "Bad dates".
7. If a changed area is in a `ONE-PAGER.md` diagram, update the diagram.
8. Update the `CLAUDE.local.md` block.
9. Stamp:
   - A note with no affected changes counts as verified. Generated files under "Uncovered changes" (`CHANGELOG.md`, lock files, release metadata) need no note.
   - If you verified every affected note and assigned every other uncovered change, run `python3 $S stamp <root>`.
   - Otherwise, run `python3 $S stamp <root> <note> ...` with only the notes that you verified.
10. Run `status` again. Do the finish checklist.

Do not re-verify notes in `investigations/`. They are frozen.

## capture

1. If this session found no durable, non-obvious fact, tell the user and stop.
2. Write the fact as one line: the claim, a `path:line` citation, and a marker.
3. Select the file for the fact:
   - A bug goes in `known-issues.md`.
   - A gotcha goes in `gotchas.md`.
   - Other facts go in the note whose `covers` glob matches the cited file. Read `manifest.json` to find it.
   - If no glob matches, use the closest topic note. Add the cited path to that note's `covers`.
4. Add the line under the correct section of the selected note. If a legacy heading conflicts with the marker (for example "Probable" for a `Confirmed:` line), add the line under a heading that matches it. Create "Confirmed bugs" if necessary. Recommend `/repo-docs audit`.
5. If the fact contradicts a line in another note, fix that line too.
6. Do not run `stamp`. You did not verify the full note.
7. Do not change `CLAUDE.local.md` unless the fact is a new top gotcha or top bug.
8. Tell the user the file and the line that you added.

## audit

Use this mode to adopt an existing `.docs/` folder or to check its health. Do not regenerate the notes.

1. Read `references/layout.md`, `references/one-pager.md`, and `references/claude-local.md`.
2. If `manifest.json` is missing, run `python3 $S init-manifest <root>`.
3. Fill `covers` for each note.
   - Before step 4 removes legacy freshness lines (for example "Notes written DATE from `main` at `sha`", `verified-at:`, YAML `baseline_commit`), copy that SHA into the note's `sha` and that date into its `checked` in `manifest.json`.
   - A legacy SHA is a better base than the file date. If the SHA is not in history, keep only the date.
4. Make a proposal list. Show it to the user and wait for approval before you change existing files:
   - Ticket, snapshot, and one-time notes to move to `investigations/`.
   - Person-named files to merge into `open-questions.md`.
   - Bug lists in README, topic notes, or `CLAUDE.local.md` to move into `known-issues.md`.
   - Gotcha lists to move into `gotchas.md`.
   - Files to rename to layout names (for example `latent-bugs.md` to `known-issues.md`).
   - `CLAUDE.local.md` content that duplicates `.docs/`, to move into the managed block.
   - Legacy freshness metadata to remove: YAML front matter, `verified-at:` lines, and lines such as "Notes written DATE from `main` at `sha`" or "Last full review: DATE". After removal, the only freshness line is the line that `stamp` writes.
5. Do the approved changes. Update `manifest.json` entries to the new paths. Set `"frozen": true` on `investigations/` notes.
6. Create missing core files: `README.md`, `known-issues.md`, `gotchas.md`, and `ONE-PAGER.md`. Add each new file to `manifest.json` and to the README index.
7. Change markers to the prefix form `Confirmed:` or `Inferred:`.
8. Report these items to the user. Do not fix them:
   - Files with more than 300 lines (`wc -l`).
   - Notes without a `path:line` citation.
   - Time-bound lines with no `as of` date, or a date older than 30 days.
   - Notes that are byte copies of tracked files:
     `find .docs -name '*.md' | while read -r f; do git ls-files -s | grep -q " $(git hash-object "$f") " && echo "$f"; done`
   - Files that do not fit the layout.
9. Write or update the `CLAUDE.local.md` block.
10. Run `python3 $S stamp <root> <note> ...` for only the notes that you checked against the code. If you checked all notes, run `stamp` with no note names.
11. Do the finish checklist.

## Finish checklist

Do these checks at the end of each run:

1. `python3 $S status <root> --committed` shows no affected note and no broken citation for the areas that you verified.
2. The `CLAUDE.local.md` block has 50 lines or fewer, and the full file has about 80 lines or fewer.
3. The `README.md` index lists each file in `.docs/`.
4. Each new claim has a `path:line` citation and a `Confirmed:` or `Inferred:` marker.
5. `git status --porcelain` shows no new tracked change from this run.

## Common mistakes

| Mistake (seen in baseline runs) | Correct action |
|---|---|
| A new freshness scheme: `verified-at:` headers, YAML front matter, a `check-stale.sh` script | Use `manifest.json`, `docs_state.py`, and the `Checked` line from `stamp` (Contract 1) |
| New names and folders: `latent-bugs.md`, `reference/`, `plans/` | Use the layout names. Only `investigations/` is a subfolder (Contract 2) |
| Marker words such as "Verified", "Read", "Probable", lowercase "inferred" | `Confirmed:` or `Inferred:` only (Contract 3) |
| A bug checked in the code filed as "probable" | Code you read and traced is `Confirmed:` (Contract 3) |
| `CLAUDE.local.md` not created or not synced | Update the block in each init, update, and audit run (Contract 8) |
| Files deleted or moved with no question | Show the list and wait for approval (Contract 5) |
| `questions-for-<name>.md` renamed to `open-questions-<name>.md` | Merge into `open-questions.md` (Contract 6) |
| Update edits one note and skips citations and dated lines | Act on each `status` group: broken citations and stale statements too (update steps 5 and 6) |
| A captured fact put in a catch-all file | Select the note by `covers` glob (capture step 3) |
| A 1-pager of 120 lines with 4 diagrams and a gantt chart | Under 80 lines, 2 or 3 flowcharts or sequence diagrams (`references/one-pager.md`) |
| Audit or update edits started with no backup | Back up `.docs/` and `CLAUDE.local.md` first ("Before any mode" step 6) |
| Run `stamp` with no note names right after audit | Stamp only notes you checked against the code. Run `update` next, so it checks each note against the changes since that note's own date or SHA |
| Old broken citations skipped as "pre-existing" | Fix every line under "Broken citations" (update step 5) |
| Only one note stamped because `CHANGELOG.md` is uncovered | Generated files need no note. Run `stamp` with no note names (update step 9) |
| A `Confirmed:` line put under a legacy "Probable" heading | Use a heading that matches the marker (capture step 4) |
