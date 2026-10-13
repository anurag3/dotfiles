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

**Minimum code that solves the problem. Nothing speculative. Governs scope of new code. For edits to existing code, see Surgical Changes below.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Always follow YAGNI principles: never implement something "for future use". Implement only what's needed right now.
- Prefer one-liners over multi-line solutions when clarity isn't sacrificed.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

Example: asked for "a function to parse dates" - write the function. Don't add a `DateParser` class with configurable formats nobody asked for.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess. Governs edits to existing code. For scope of new code, see Simplicity First above.**

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
- List what was stripped for the user to confirm. Don't carry another team's or repo's specifics silently into new code.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, give each step a check, and run the check before you call the step done: `[Step] → verify: [check]`.

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Plan Execution Approach

**Execute multi-task plans in parallel waves of `implementer` subagents. Do not use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Skip the "Execution Handoff" choice prompt in `superpowers:writing-plans` and proceed.**

Plan format (add to every plan that `superpowers:writing-plans` or plan mode writes):

- Each task has a `Files:` list of every file that the task creates or changes.
- Each task has a `Depends on:` line with task numbers, or `none`.

To execute or resume a plan, including after compaction, invoke the `executing-plans-in-waves` skill first.

Exception: for a single task with no plan, dispatch one `implementer` directly. Only deviate if the user explicitly asks for inline execution or another approach.

`plan-file-location-guard.py` replaces the superpowers subagent-driven-development header in plan files.

## 6. Spec & Plan File Location

**Write every spec, design doc, RFC, and plan to these paths, with no exceptions. This overrides any skill default, such as superpowers' `docs/superpowers/specs/...`.**

- Specs: `~/.claude/specs/<repo>/<YYYY-MM-DD>-<description>/<description>_spec.md`
- Plans: `~/.claude/plans/<repo>/<YYYY-MM-DD>-<description>/<description>_plan.md`

`<repo>` = repo name from `git remote get-url origin` (last path segment, strip `.git`), else `basename "$PWD"`. `<description>` = 2-5 word kebab-case summary (e.g. `add-auth-middleware`). `mkdir -p` the directory before writing. This applies to every trigger: brainstorming's "write design doc" step, the writing-plans skill, plan mode, or a direct request.

These paths are for local use only. Never put them in a commit message or PR body (rule 13).

`plan-file-location-guard.py` blocks other paths, including `docs/superpowers/`.

## 7. Worktree Policy

**Never create a git worktree unless the user explicitly asks for one. Work in the current workspace and branch.** The deny list and `git-safety-guard.py` block worktrees.

## 8. Simplified Technical English + ad-concise + ad-concise's ADHD structure rules for File Content

**Before you write technical documentation, a README, a procedure, a code comment block, or an error/UI string, invoke the `simplified-technical-english` skill first. Do not rely on description-matching to trigger it.** This applies to file content authored for a human reader. Conversational replies follow the ad-concise output style.

File content combines all three, with this precedence:

- **STE is primary.** Controlled-language rules (approved word list, grammar, sentence structure) come from `simplified-technical-english`.
- **ad-concise fills the gaps.** Where STE is silent, apply `ad-concise`'s tone rules: no em-dash, no filler words, no sycophancy, no LLM-isms.
- **ad-concise's ADHD structure rules shape structure**, in every authored file including code comments: lead with the point, number multi-step procedures, make the actionable part visible first. This does not override the existing no-comments-unless-WHY rule. It governs style when a comment is written, not whether to write one.

## 9. Databricks Command Confirmation

**Never run a Databricks command without confirming with the user first.** This includes the CLI, `dbt` invocations against a Databricks target, SQL against a warehouse, job/pipeline triggers, and cluster operations. It also includes commands that look read-only (`dbt test`, `dbt run`, `databricks bundle validate`) when they execute against a live workspace/warehouse. State the exact command and its target (profile, catalog, schema, warehouse) and wait for explicit approval before executing. Applies on top of any Databricks skill's own guidance. After the user approves, prefix the command with `ALLOW_DATABRICKS_RUN=1`.

## 10. Sample Before Querying Databricks Tables

**Before running any non-trivial SQL against a Unity Catalog table (aggregations, multi-column `CASE WHEN` rollups, joins, or anything without a `LIMIT`), first confirm the table's real structure and rough size in the same session. Never guess column names from memory or naming conventions.**

Invoke the `sampling-databricks-tables` skill first. Prefer Genie One (`databricks genie ask`) for data questions in general.

## 11. Reviewer Agents Use sam-review

**Whenever an agent is dispatched to review code (a PR, a local diff, or a branch), instruct it to follow the `sam-review` skill's workflow, not an ad-hoc review or the generic `code-review` skill.** Applies whether or not a PR URL is present. When there is no PR URL, the dispatched agent adapts `sam-review`'s checklist (data pipelines, infra, ML, backend/API coverage) to the local diff instead of a PR page. State this instruction explicitly in the dispatch prompt, since a fresh agent has no memory of this rule.

## 12. Conventional Commits

**Every git commit message and every branch name MUST follow Conventional Commits style, with no exceptions. Never put a skill name in either.**

- Commit message subject: `<type>: <description>`, e.g. `fix: correct null check in foo()`.
- Branch name: `<type>/<description>`, e.g. `fix/null-check-in-foo`, kebab-case description.
- `<type>` is one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`, `build`. Pick it from the actual nature of the change (new capability → `feat`, bug fix → `fix`, cleanup/deps/tooling → `chore`, docs-only → `docs`, no-behavior-change restructuring → `refactor`, test-only → `test`).
- `git-convention-guard.py` enforces this.

## 13. Commit/PR Content: No Attribution, No Internal Artifacts

**A git commit message and a PR description must state only what the change does, not how it was produced. Applies to both surfaces equally, across every repo.**

- Banned: AI-attribution lines or footers, rule 6 spec/plan paths, and task/round bookkeeping ("Task 3", "fix round 1", "per the plan").
- `git-convention-guard.py` enforces this.
- Before opening a PR, spot-check `git log <base>..<branch>` for any commit that does not obey rules 12 and 13. The hook does not check commits that existed before it.
- A commit/PR body should read like a summary + test plan (what changed, why, how it was verified), not a narration of the session that produced it.

## 14. Standing Reply Shaping: ad-concise

The `ad-concise` output style (set in settings.json) shapes conversational replies.
