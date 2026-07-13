---
name: plan-file-location
description: Use before writing any plan file — triggered by entering plan mode (EnterPlanMode), by the superpowers:writing-plans skill, or by any user request to write/create/draft a plan. Defines the required file path and naming convention, overriding any harness-suggested path. Invoke this FIRST, before writing plan content anywhere.
---

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
