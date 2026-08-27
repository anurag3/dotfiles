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

## 7. Worktree Policy

**Never create a git worktree for isolation — via `superpowers:using-git-worktrees`, `subagent-driven-development`'s Setup step, or any other skill — unless the user explicitly asks for one; work directly in the current workspace/branch by default.**
