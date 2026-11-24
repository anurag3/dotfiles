# `.docs/` layout and templates

Use these file names and templates in each repo. Do not add other subfolders or other naming schemes.

## Core files

Each repo has all of these files.

| File | Content | Why it helps Claude |
|---|---|---|
| `README.md` | Opening line, the `Checked` line from `stamp`, marker legend, `\| File \| Topic \|` index. No bug lists: link to `known-issues.md` | The first file to read. It routes to the correct note |
| `ONE-PAGER.md` | Human summary: purpose, inputs and outputs, 2 or 3 Mermaid diagrams, top 5 risks, where to start. See `one-pager.md` | Gives a person the full system in one page |
| `code-flow.md` | Entry points, run order, components, and how they call each other | Shows where a change starts and what it calls |
| `data-flow.md` | Sources, tables, topics, files, transforms, sinks, external dependencies | Shows what data a change touches upstream and downstream |
| `gotchas.md` | The only home for gotchas. Grouped by area. One line each, with `path:line` | Stops repeated mistakes. One list, so no drift |
| `known-issues.md` | The only home for bugs. Sections: Confirmed bugs, Inferred bugs, Doc drift, Resolved | One list, so bug lists do not drift between files |
| `improvements.md` | Possible improvements, ranked by value and effort | Gives a ready backlog when the user asks what to fix |
| `<topic>.md` | One note for each component or flow | Holds the detail for one area. Claude reads only the note it needs |

## Optional files

Create each file only when the repo has content for it.

| File | Content | Why it helps Claude |
|---|---|---|
| `change-recipes.md` | "To add X, change these files together." Version pins that move together | Highest value for edits. Stops partial changes |
| `glossary.md` | Domain terms, ID formats, abbreviations | Stops wrong guesses about domain words |
| `contracts.md` | Upstream and downstream systems, tables, topics, APIs. Link to the sibling repo's `.docs/` file. Do not copy it | Shows what breaks outside the repo |
| `runbook.md` | Run locally, debug a failed job, backfill, where logs are | Gives the exact commands to run |
| `testing.md` | How to test, what CI checks, test gaps | Shows which tests prove a change |
| `decisions.md` | Why the code is as it is, from git log and PRs | Stops changes that undo a decision |
| `open-questions.md` | Open items. Each line names the person to ask | One place for questions. No person-named files |
| `investigations/` | Ticket, snapshot, and one-time analysis notes | Keeps dated work apart from durable notes. `update` does not check them again |

## Rules for every note

1. Cite `path:line` (or `path:start-end`) in backticks for each code claim. The state script finds broken citations only in this form.
2. Use the markers `Confirmed:` and `Inferred:` as a prefix. Use no other marker words. See `bug-hunting.md` for the evidence bar.
3. Write each time-bound statement (open PR, rollout status, data count) with `as of YYYY-MM-DD`. `status` reports dates older than 30 days.
4. Keep each file under 300 lines. If a file is longer, split it into topic notes.
5. Do not hard-wrap lines.
6. Do not restate the repo's README, AGENTS.md, or CLAUDE.md. Link to them. Record only what they do not show, or where they are wrong (Doc drift).
7. Write in Simplified Technical English: short sentences, one idea in each sentence, no em-dashes.
8. Do not write a `Checked` line, front matter, or other metadata. `stamp` writes the `Checked` line.

## README.md template

```markdown
# Local notes index

These notes are local and git ignores them. They record facts that the code and the repo docs do not show. Start with the file for your task area.

Markers: `Confirmed:` means checked in source code, a test, or a run. `Inferred:` means concluded from reading, not checked. Verify an `Inferred:` claim before you act on it.

Bugs are in [known-issues.md](known-issues.md). Gotchas are in [gotchas.md](gotchas.md).

| File | Topic |
|---|---|
| [ONE-PAGER.md](ONE-PAGER.md) | Summary for people: purpose, diagrams, top risks |
| [code-flow.md](code-flow.md) | Entry points, run order, components |
| [data-flow.md](data-flow.md) | Sources, tables, sinks |
| [gotchas.md](gotchas.md) | Traps, grouped by area |
| [known-issues.md](known-issues.md) | Bugs, doc drift, resolved items |
| [improvements.md](improvements.md) | Ranked improvement scope |
| [loader.md](loader.md) | Autoloader run flow, merge logic |
```

Do not write a `Checked` line. `stamp` adds it under the H1.

## Topic note template

```markdown
# Loader

## Purpose

Two or three sentences: what the component does and who calls it.

## Entry points

- `loader/main.py:12` `main()`: CLI entry. The job `load_daily` in `databricks.yml:40` calls it.

## Code flow

1. `main()` parses arguments (`loader/main.py:20-35`).
2. ...

## Data flow

| Reads | Writes | Evidence |
|---|---|---|
| `raw.events` | `bronze.events` | `loader/merge.py:44` |

## Config

| Key | Default | Effect | Evidence |
|---|---|---|---|

## Failure modes

| Condition | What happens | Evidence |
|---|---|---|
| Source folder is empty | The merge writes 0 rows and the job passes | `loader/merge.py:60-66` |

## Open questions

- Inferred: ... (ask the owner, see `open-questions.md`).

Gotchas: see [gotchas.md](gotchas.md#loader). Bugs: see [known-issues.md](known-issues.md).
```

Omit a section that has no content. A "What happens / Evidence" table is the best form for failure modes and fallbacks.

## known-issues.md template

```markdown
# Known issues

## Confirmed bugs

- Confirmed: `loader/merge.py:88` The INSERT lists `foreign_source, foreign_id` in the opposite order of the table columns. Effect: each row stores the source in the ID column. Evidence: column order in `sql/create_events.sql:5-9`.

## Inferred bugs

- Inferred: `loader/merge.py:60` The MERGE condition `t.event_id = s.event_id` is never true for a null `event_id`. Effect: each run inserts those rows again. Evidence: no null filter before the MERGE. No run checked the duplicates.

## Doc drift

- Confirmed: `README.md:40` says the job runs hourly. `databricks.yml:52` has no schedule. Airflow starts the job (`dags/load.py:18`).

## Resolved

- `loader/main.py:149` wrong Spark config key. Fixed in `3f2a9c1e` (2026-11-20).
```

Each item has three parts: the marker and `path:line` with the claim, the effect, and the evidence. In "Resolved", add the fixing SHA and date.

## gotchas.md template

```markdown
# Gotchas

## Loader

- `loader/sample.py:14` samples with `LIMIT` and no `ORDER BY`. Joins between two sampled tables mostly miss.

## Build and deploy

- Change the dbt-databricks pin in `pyproject.toml` and `databricks.yml:12` together.
```

One line for each gotcha. Group by area. Use the same area names as the topic notes, so a topic note can link to `gotchas.md#<area>`.

## Investigation note header

Each file in `investigations/` starts with this header. The manifest marks it `"frozen": true`, so `update` does not check it again.

```markdown
# DS-59 duplicate domains

- Date: 2026-11-04
- Ticket: DS-59
- Data source: `prod.silver.company_domains`, snapshot of 2026-11-04
```

## manifest.json

`init-manifest` creates the file. It sets `checked` for each note from the file date and leaves `sha` null. Audit copies legacy SHAs into `sha`. `stamp` writes `sha`, `checked`, `branch`, and `generated`. You edit only `covers`, new note entries, and `frozen`.

```json
{
  "branch": "main",
  "sha": "a1abbff1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7",
  "generated": "2026-11-23",
  "files": {
    "README.md": {"covers": []},
    "code-flow.md": {"covers": ["src/main.py", "databricks.yml"], "sha": "a1abbff1...", "checked": "2026-11-23"},
    "loader.md": {"covers": ["loader", "sql/*.sql", "tests/**/test_loader*.py"], "sha": "a1abbff1...", "checked": "2026-11-23"},
    "investigations/ds59-duplicate-domains.md": {"covers": [], "frozen": true}
  }
}
```

`covers` glob rules. Paths are relative to the repo root. Only `*`, `**`, and bare paths work. Do not use `?` or `[...]`.

| Pattern | Matches |
|---|---|
| `loader` (no wildcard) | The file `loader`, or each file under the directory `loader/` |
| `sql/*.sql` | `.sql` files directly in `sql/`. `*` matches one path segment only |
| `macros/**` | Each file under `macros/`, at any depth |
| `tests/**/test_loader*.py` | `tests/test_loader.py` and the same name in any subdirectory |

To add a new note, add an entry `"<name>.md": {"covers": [...]}` to `files`, then run `stamp` for that note. A note that is not in the manifest cannot be stamped.
