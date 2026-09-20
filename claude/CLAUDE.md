@RTK.md

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

Example: asked to "cache this" - clarify in-memory per-request vs. persistent across restarts. Don't pick one silently.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative. Governs scope of new code — for edits to existing code, see Surgical Changes below.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Always follow YAGNI principles: never implement something "for future use" — only what's needed right now.
- Prefer one-liners over multi-line solutions when clarity isn't sacrificed.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

Example: asked for "a function to parse dates" - write the function. Don't add a `DateParser` class with configurable formats nobody asked for.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess. Governs edits to existing code — for scope of new code, see Simplicity First above.**

Example: asked to fix a null check in `foo()` - fix it. Don't reformat the file or rename nearby variables while you're in there.

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

When copying a pattern from a reference repo:

- Strip every repo-specific value (alert emails, team names, variable descriptions, IDs) before applying to the new target.
- List what was stripped for the user to confirm — don't carry another team's or repo's specifics silently into new code.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Plan Execution Approach

**Default to subagent-driven development (`superpowers:subagent-driven-development`) for executing multi-task plans — skip the "Execution Handoff" choice prompt in `superpowers:writing-plans` and just proceed.**

Exception: a single isolated task with no multi-task plan behind it — dispatch a subagent directly via the Agent tool instead. The skill's ledger, review gate, and fix-loop exist to survive a long unattended multi-task run; for one task there's nothing for them to coordinate. Otherwise, only deviate if the user explicitly asks for inline execution or another approach.

## 6. Spec & Plan File Location

**Every spec/design doc/RFC and every plan MUST be written to these paths, no exceptions — this overrides any skill-suggested default (e.g. superpowers' `docs/superpowers/specs/...`):**

- Specs: `~/.claude/specs/<repo>/<YYYY-MM-DD>-<description>/<description>_spec.md`
- Plans: `~/.claude/plans/<repo>/<YYYY-MM-DD>-<description>/<description>_plan.md`

`<repo>` = repo name from `git remote get-url origin` (last path segment, strip `.git`), else `basename "$PWD"`. `<description>` = 2-5 word kebab-case summary (e.g. `add-auth-middleware`). `mkdir -p` the directory before writing. Applies regardless of trigger — brainstorming's "write design doc" step, the writing-plans skill, plan mode, or a direct request to draft one.

These paths are for local use only — never put them in a commit message or PR body (rule 13).

## 7. Worktree Policy

**Never create a git worktree for isolation — via `superpowers:using-git-worktrees`, `subagent-driven-development`'s Setup step, or any other skill — unless the user explicitly asks for one; work directly in the current workspace/branch by default.**

## 8. Simplified Technical English

**Before writing any technical documentation, README, procedure, code comment block, or error/UI string, invoke the `simplified-technical-english` skill first — do not rely on description-matching to trigger it.** Applies to file content authored for a human reader; does not apply to your own conversational replies, which follow the `ad-concise` output style instead.

## 9. Databricks Command Confirmation

**Never run a Databricks command — CLI, `dbt` invocations against a Databricks target, SQL against a warehouse, job/pipeline triggers, cluster operations, etc. — without confirming with the user first.** This includes commands that look read-only (`dbt test`, `dbt run`, `databricks bundle validate`) when they execute against a live workspace/warehouse. State the exact command and its target (profile, catalog, schema, warehouse) and wait for explicit approval before executing. Applies on top of any Databricks skill's own guidance.

## 10. Sample Before Querying Databricks Tables

**Before running any non-trivial SQL against a Unity Catalog table (aggregations, multi-column `CASE WHEN` rollups, joins, or anything without a `LIMIT`), first confirm the table's real structure and rough size in the same session — never guess column names from memory or naming conventions.**

1. `databricks experimental aitools tools discover-schema <catalog.schema.table> --profile <PROFILE>` — one call returns real column names/types, 5 sample rows, null counts, and total row count. Fall back to `DESCRIBE TABLE` plus a manual `SELECT * FROM <table> LIMIT 10` only if discover-schema isn't available.
2. For file/storage size specifically (`numFiles`, `sizeInBytes`, not returned by discover-schema), use `DESCRIBE DETAIL <table>` instead of `COUNT(*)` — `COUNT(*)` is metadata-only on a plain Delta table with no filter, but forces a full scan on views, external/non-Delta tables, and streaming tables.
3. Only then write the full aggregation/join query.
4. When measuring match rates or coverage between two datasets/tables, use `LEFT JOIN` (not `INNER JOIN`) and count non-null matches — an `INNER JOIN` silently drops every row that didn't match, trivially reporting 100% match regardless of actual coverage.

Skip this only when the columns were already confirmed earlier in the same session. Prefer Genie One (`databricks genie ask`) for data questions in general — it resolves schema/joins itself, sidestepping this class of mistake entirely.

## 11. Reviewer Agents Use sam-review

**Whenever an agent is dispatched to review code — a PR, a local diff, or a branch — instruct it to follow the `sam-review` skill's workflow, not an ad-hoc review or the generic `code-review` skill.** Applies whether or not a PR URL is present; when there is no PR URL, the dispatched agent adapts `sam-review`'s checklist (data pipelines, infra, ML, backend/API coverage) to the local diff instead of a PR page. State this instruction explicitly in the dispatch prompt, since a fresh agent has no memory of this rule.

## 12. Conventional Commits

**Every git commit message and every branch name MUST follow Conventional Commits style — no exceptions, and never a skill name in either.**

- Commit message subject: `<type>: <description>`, e.g. `fix: correct null check in foo()`.
- Branch name: `<type>/<description>`, e.g. `fix/null-check-in-foo`, kebab-case description.
- `<type>` is one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`, `build` — picked from the actual nature of the change (new capability → `feat`, bug fix → `fix`, cleanup/deps/tooling → `chore`, docs-only → `docs`, no-behavior-change restructuring → `refactor`, test-only → `test`).
- Never put a skill name (e.g. `ponytail`, `ponytail-audit`) in a branch name, commit message, or PR title/description — name them after what the change does, not the skill that produced it.

## 13. Commit/PR Content: No Attribution, No Internal Artifacts

**A git commit message and a PR description must state only what the change does — nothing about how it was produced. Applies to both surfaces equally, across every repo.**

- Never append "🤖 Generated with Claude Code" or any similar AI-attribution line, byline, or footer, to a commit message or PR body — regardless of any tool default that suggests one.
- Never reference internal planning artifacts: no paths to the rule 6 spec/plan locations (`~/.claude/plans/...`, `~/.claude/specs/...`), no mentions of "the plan," no ledger/task/round bookkeeping language (e.g. "Task 3", "fix round 1", "per the plan"). This is in addition to the skill-name ban in rule 12.
- Before opening a PR, spot-check `git log <base>..<branch>` for any commit that already slipped one of these in — commits are often written earlier in a session, before this rule is top of mind.
- A commit/PR body should read like a summary + test plan (what changed, why, how it was verified) — not a narration of the session that produced it.
