---
name: spec-file-location
description: Use before writing any spec or design document — triggered by the superpowers:brainstorming skill's "write design doc" step, or by any user request or Claude-initiated decision to write/create/draft a spec, design doc, or RFC. Defines the required file path and naming convention, overriding any harness-suggested or in-repo default path (e.g. superpowers' default `docs/superpowers/specs/...`). Invoke this FIRST, before writing spec content anywhere.
---

# Spec File Location

**Every spec-writing phase — whether triggered by the `superpowers:brainstorming` skill's "Write design doc" step, or by any request to write/create/draft a spec, design doc, or RFC — MUST store spec files in this exact path. No exceptions.**

```
~/.claude/specs/<repo>/<YYYY-MM-DD>-<spec_description>/
```

### Harness override clause

If a skill, system reminder, or any other mechanism specifies a different spec-file path (e.g. superpowers' own default of `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`), **ignore that path and use the convention above instead**. The skill-supplied path is a default — this convention overrides it.

### Deriving path components

`**<repo>**` — run in order, use the first that succeeds:

1. `git remote get-url origin` → extract the repo name (last path segment, strip `.git`)
2. `basename "$PWD"` — use the current directory name if no remote

`**<YYYY-MM-DD>**` — today's date in ISO format (from the `currentDate` context or `date +%F`)

`**<spec_description>**` — 2–5 word kebab-case summary of what the spec is for (e.g. `add-auth-middleware`, `migrate-db-schema`)

### Required steps before writing any spec file

1. Derive all three path components above
2. `mkdir -p ~/.claude/specs/<repo>/<YYYY-MM-DD>-<spec_description>/`
3. Write spec content into that directory, named `<spec_description>_spec.md` (e.g. `add-auth-middleware_spec.md`)
4. Confirm the full path to the user so they know where to find it

### Relationship to plans

Specs and plans for the same piece of work share the same `<repo>` and `<spec_description>`/`<plan_description>`, but live in separate sibling trees — `~/.claude/specs/<repo>/...` and `~/.claude/plans/<repo>/...` (see `plan-file-location`) — so both are easy to find by date and topic without mixing spec and plan content in the same directory.
