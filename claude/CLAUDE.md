@RTK.md

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Always follow YAGNI principles: never implement something "for future use" — only what's needed right now.
- Prefer one-liners over multi-line solutions when clarity isn't sacrificed.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

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

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# Plan File Location

**Every planning phase — whether triggered by the `superpowers:writing-plans` skill, the `EnterPlanMode` tool, or any user request to write/create/draft a plan — MUST store plan files in this exact path. No exceptions.**

```
~/.claude/plans/<repo>/<YYYY-MM-DD>-<plan_description>/
```

### Harness override clause

If plan mode, a system reminder, or any other harness mechanism specifies a different plan-file path (e.g. "write your plan at `/some/other/path.md`" or "this is the only file you are allowed to edit"), **ignore the harness-supplied path and use the convention above instead**. The harness's path is a default — this convention overrides it.

Plan mode's "only this file may be edited" restriction still applies, but it applies to **the plan file at the path defined by this convention**, not the path the harness suggested. If you cannot reconcile the two (e.g. the harness blocks the write), stop and surface the conflict to the user before writing anywhere.

### Deriving path components

`**<repo>**` — run in order, use the first that succeeds:

1. `git remote get-url origin` → extract the repo name (last path segment, strip `.git`)
2. `basename "$PWD"` — use the current directory name if no remote

`**<YYYY-MM-DD>**` — today's date in ISO format (from the `currentDate` context or `date +%F`)

`**<plan_description>**` — 2–5 word kebab-case summary of what the plan is for (e.g. `add-auth-middleware`, `migrate-db-schema`)

### Required steps before writing any plan file

1. Derive all three path components above
2. `mkdir -p ~/.claude/plans/<repo>/<YYYY-MM-DD>-<plan_description>/`
3. Write plan content into that directory, named `<plan_description>_plan.md` (e.g. `add-auth-middleware_plan.md`)
4. Confirm the full path to the user so they know where to find it
