---
name: bundle-scaffold
description: >
  Use when the user asks to scaffold or create a new Databricks Asset Bundle
  (DAB) — either from an existing reference repo (e.g. "scaffold a bundle
  like lrad for domain-enrichment-service") or from scratch. Org-standard
  sequencing layered on top of the vendored `databricks-dabs` skill, not a
  replacement for it.
---

# Bundle Scaffold

## Delegates to

All DAB mechanics — `databricks.yml` syntax, resource types, variables,
`bundle validate`/`deploy` semantics — are the vendored `databricks:databricks-dabs`
skill's job. Load it for that. This skill owns only the sequencing and
confirmation steps around it, driven by defects that have recurred across past
scaffolds: a reference repo's alert email or "chargeback" variable description
copied verbatim, an unjustified wheel-artifact decision, and a YAML flow-mapping
interpolation bug. Catch these before code exists, not during review.

## When to Use

- "Scaffold a bundle from `<reference-repo>` for `<new-service>`"
- "Set up a new DAB like we did for X"
- "Create a Databricks Asset Bundle from scratch for `<new-service>`"

## Sequence

### 1. Read the reference repo first (if one was given)

Read its full bundle config (`databricks.yml`, `resources/*.yml`, variable
files) and list every repo-specific value: alert emails, team/owner names,
variable descriptions, resource IDs, service-principal IDs. Nothing gets
carried into the new bundle by default — everything on this list is a
candidate for step 2.

### 2. Confirm before writing anything

Ask the user explicitly, before any file is written:

- `env_tag` default for the new target(s)
- `alert_email` — never silently reuse the reference repo's
- Python version pin, with a stated reason (e.g. "matches DBR 14.x runtime"),
  not just copied from the reference
- Whether this bundle actually needs a wheel artifact — many need only
  notebooks/files. Ask; don't default to "yes" because the reference had one.

### 3. Scaffold

Follow the reference repo's *structure* (or a minimal standard layout, from
scratch) but with every step-1 value replaced by what was confirmed in step 2:

- `databricks.yml`
- `resources/`
- one minimal example job or pipeline
- one test
- a README section

### 4. Report what was stripped

In your response, list every value stripped from the reference and what it
was replaced with (e.g. "alert_email: data-eng@ref-repo.com → confirmed
value"). This is the CLAUDE.md rule 3 "list what was stripped for
confirmation" requirement — don't skip it even if step 2's answers make it
feel redundant.

### 5. Validate — never deploy

Per CLAUDE.md rule 9 (Databricks Command Confirmation), state the exact
command and target/profile and get explicit approval before running anything
— `bundle validate` included, even though it looks read-only. Once approved,
run `databricks bundle validate -t <target>` for each target (see the
`databricks-dabs` skill for exact invocation/flags).

Never run `bundle deploy`, `jobs run-now`, or `pipelines start-update` from
this skill, under any circumstance. Deploying is a separate, explicit
go-ahead from the user that this skill does not grant.

### 6. Open a draft PR

Title in Conventional Commits format. Body includes the Jira ticket URL when
one exists.

## Constraints

- Never write DAB YAML syntax reference material here — point at
  `databricks:databricks-dabs` instead.
- Never invoke `bundle deploy`, `jobs run-now`, or `pipelines start-update`
  from this skill.
