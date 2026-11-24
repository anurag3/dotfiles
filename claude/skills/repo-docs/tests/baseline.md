# repo-docs: baseline and skill runs

Scenarios run on scratch clones. Model: sonnet, general-purpose subagent. Date: 2026-11-23.

| ID | Repo | Request |
|---|---|---|
| A | Airflow DAG repo (no `.docs`) | Create `.docs` with code specifics, data flow, code flow, improvements, gotchas, latent bugs, 1-pager with diagrams. Keep it current as code changes |
| B | Scala and Spark monorepo (`.docs` at a recorded SHA, HEAD 3 commits ahead) | Update `.docs` for code changes since the last generation |
| C | dbt project on Databricks (`.docs` + `CLAUDE.local.md`) | A feature commit merged. Save non-obvious facts about it to the local notes |
| D | dbt pipeline repo (17 files, no index) | Clean up and standardize `.docs`. Add what is missing. Keep all facts |

## Baseline (no skill)

Content quality was high in all four runs: `path:line` evidence, real latent bugs, doc drift found. The failures are in structure and state, not in content.

### Failures

1. **Each run invents its own freshness scheme.** Three runs, three schemes:
   - A: header lines `verified-at:` / `verified-date:` / `covers:` in each note, plus `.docs/check-freshness.sh`.
   - B: reads and rewrites a prose line in README ("Updated 2026-11-23 to `master` at `aac3479f`"). Works only because the README had a SHA.
   - D: YAML front matter (`baseline_commit`, `depends_on`, `verification`), plus `.docs/tools/check-stale.sh`.
2. **Each run invents its own layout and names.** `one-pager.md` vs other names. `latent-bugs.md` (A, D) vs `known-issues.md` (existing). D added `reference/ data/ ops/ plans/` subfolders. A has a 167-line DAG catalog.
3. **Marker words differ in every run.** A: "Read" / "Verified". C: "Probable (not confirmed)". D: "inferred" lowercase.
4. **Marker misuse.** C filed a bug it checked in code under "Probable (not confirmed)" and said so in its report.
5. **`CLAUDE.local.md` never touched.** 0 of 4 runs created or synced it. C did not consider it.
6. **Destructive changes without asking.** D deleted 2 files and moved 15 files with no confirmation.
7. **Person names kept.** D renamed `questions-for-<name>.md` to `plans/open-questions-<name>.md`.
8. **Update did not check citations or time-bound text.** B edited one note and the README line. It did not look for broken `path:line` or dated status lines.
9. **Capture went to a catch-all file.** C put DS 67 facts into `domain-notes.md`.
10. **1-pager size.** A 113 lines with 3 diagrams. D 120 lines with 4 flowcharts and a gantt chart.

### Natural grain to keep

- A and D both made separate `gotchas.md`, `code-flow.md`, `data-flow.md`, and a bugs file. The user also asked for these by name. The skill uses them as core files.
- A and D both put the freshness data next to the notes and checked `git diff <sha> -- <paths>`. The skill keeps that idea but puts it in one script (`scripts/docs_state.py`) and one file (`.docs/manifest.json`), so no repo gets its own copy.
- D found `.docs` files that were byte copies of tracked `docs/` files. `audit` checks for this.

## With skill

Same prompts on fresh clones, plus "if a step needs approval, write the question, assume yes". The scala clone was stamped at `5a5ef0f0` with `covers` so `update` had a real base. All four runs invoked `repo-docs` and `simplified-technical-english` with no hint.

| ID | Result | Evidence |
|---|---|---|
| A | Pass | Exact layout names, manifest with `covers`, `stamp`. ONE-PAGER 76 lines, 3 flowcharts. `CLAUDE.local.md` 47 lines. 31 markers. No scripts in `.docs`. `status --committed` clean. Asked (in writing) to approve the topic list and a live Airflow run |
| B | Pass with 2 loopholes | Used `status`, `diff`, `stamp`. Changed only `databricks-loader.md`. Created the `CLAUDE.local.md` block. Loopholes: skipped 6 broken citations as "pre-existing"; stamped one note only because `CHANGELOG.md` was uncovered |
| C | Pass with 1 gap | `Confirmed:` / `Inferred:` with citations. Bugs to `known-issues.md`. Fixed a line in another note that the commit made false. No stamp. Recommended `audit` (no manifest). Gap: `Confirmed:` items under a legacy "Probable (not confirmed)" heading |
| D | Pass | Layout exact. 13 notes to frozen `investigations/` with dated headers. Person file merged into `open-questions.md`. Byte copies found and listed for deletion. ONE-PAGER 73 lines. `CLAUDE.local.md` 48 lines. `status --committed` clean |

Baseline failures 1 to 10 did not occur in any run with the skill.

### Refactor

The three loopholes from B and C were closed in SKILL.md (update step 5, update step 9, capture step 4) with rows in Common mistakes.
