---
name: sam-review
description: >
  Use when the user asks to review a pull request AND supplies a PR URL
  (e.g. "review this PR <link>", "is this PR safe to merge <link>") —
  covers data pipelines (ETL/ELT, dbt, Spark, Airflow, SQL, schema
  migrations), infrastructure (Terraform, Helm, Kubernetes, CI/CD), ML, and
  backend/API code. Requires an explicit PR link in the request.
---

# PR Review

Review as a Principal Engineer: direct, thorough, and willing to block a  
merge when something is genuinely wrong. Explain **why** something is a  
problem, not just that it is one — and call out what's done well.

## Usage

```
review this PR <PR URL>
```

Fetch the diff yourself once you have the link (works from any directory —  
`gh` resolves the repo from the URL):

```bash
gh pr view <PR URL> --json title,body,files,additions,deletions,commits
gh pr diff <PR URL> --patch > /tmp/pr<number>.diff
```

The PR's branch is usually not checked out locally — the working tree is most often
on the base branch (e.g. `develop`/`main`), which may lack the file entirely or hold
an older version of it. Derive every `Location` (`file.py:42`) citation from the diff
file's own hunk headers (`@@ -a,b +c,d @@`), not from grepping or reading the file in
the local working tree — that's the same local-checkout trap the Large PR Fan-Out
Protocol guards sub-agents against, and it applies just as much to a direct review.
Only read local files to pull in context the diff itself doesn't show (e.g. an
unchanged helper the diff calls into) — and even then, confirm via the diff that the
surrounding code is unchanged before trusting the local version's line numbers.

---

## Domain Routing

Identify which domain(s) the diff touches, then read the matching reference  
file(s) below before reviewing. A diff can span more than one domain (e.g. a  
Helm chart deploying a Spark job) — read all that apply.

| Diff touches                                                                                                | Reference file                               |
| ----------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Pipelines, ETL/ELT, dbt, Spark, Airflow, SQL, schema/warehouse changes, or ML training/serving/feature code | `references/data-engineering.md`             |
| Terraform, Helm, Kubernetes manifests, CI/CD config, cloud provisioning                                     | `references/devops-infra.md`                 |
| Application/API/service code                                                                                | `references/backend-software-engineering.md` |

Layer the domain-specific traps from those file(s) onto the core checklist  
below.

---

## Large PR Fan-Out Protocol

For a small/medium diff, review it directly — do not spawn sub-agents.

Fan out only when a single pass would blur attention across unrelated  
components (rule of thumb: >500 changed lines, or files spanning more than  
two domains/components from the Domain Routing table).

1. **Split by component, not by line count.** Group changed files into
  coherent slices (e.g. "CI/CD + deploy config", "core resolver logic",  
   "new utils package + its tests") — each slice should be reviewable on  
   its own without missing shared context. Write each slice to its own  
   diff file (`/tmp/pr<number>_<slice>.diff`). This grouping is  
   pattern-matching against the Domain Routing table — do it yourself, it  
   doesn't need a model call.
2. **Dispatch one `pr-slice-reviewer` sub-agent per slice, in parallel** —
  not `general-purpose`. It's scoped to read only the diff file it's  
   given (no `git diff`/`git show`/local-checkout access), which avoids a  
   failure mode general-purpose agents hit: reading the local checkout  
   instead of the PR branch and reporting findings that don't exist on the  
   branch. Give each agent:
  - The path to its diff file.
  - The path to the relevant `references/<domain>.md` file(s) — point at  
  the file, don't paste the checklist inline.
  - Nothing else; its system prompt already has the core checklist and  
  output format baked in.
3. **Reconcile before consolidating** — do not just concatenate sub-agent
  outputs into the final report:
  - Re-verify every 🔴/🟡 finding against the actual diff text yourself  
  before including it. A sub-agent flagging something you're not fully  
  sure of is a signal to check, not a fact to pass through.
  - Check for cross-slice issues no single slice-scoped agent could see:  
  a shared module changed in one slice and consumed in another, a  
  schema/contract produced in one slice and read in another, logic  
  duplicated across slices.
  - Deduplicate findings raised by more than one slice.
  - Emit exactly one consolidated report in the Output Format below —  
  never return the per-slice tables as-is.

### Model & cost guidance

- Splitting the diff into slices (step 1) is pattern-matching, not  
judgment — do it directly rather than spending a model call on it.
- Section reviews (step 2) need the same reasoning tier as the main  
review. Missing a subtle correctness/security/architecture issue costs  
far more (a bad merge, or rework re-reviewing) than a smaller model  
saves in tokens — don't downgrade these.
- The reconciliation step (step 3) is where cross-slice issues and  
sub-agent misreads get caught — keep it on the main review thread, not  
delegated to another agent.

---

## Review Checklist

Work through all three areas for every review. Do not skip a category because  
the PR looks small — subtle issues often hide in small changes.

### 🔴 Pain Points (Obvious Issues)

- Logic errors, off-by-one mistakes, silent failures
- Missing error handling or no retry logic on flaky operations
- Hardcoded values that should be config- or environment-driven (12-Factor config)
- Missing, misleading, or excessively noisy logging
- Tests that are absent, trivial, or structured in a way that can't catch regressions
- Breaking changes to contracts (schema, API, file format, column names) with no migration plan
- Functions or tasks doing too much — no clear single responsibility (SRP)
- **Speculative generality** *(🟢 Minor)*: config knobs, flags, or abstraction layers built for a hypothetical future need with no current caller (YAGNI)
- **Needless complexity** *(🟢 Minor; 🟡 Major if it obscures a correctness issue)*: extra layers, indirection, or cleverness for a problem a simpler approach would solve (KISS)
- **Duplicated logic** *(🟢 Minor; 🟡 Major if copies have already drifted)*: copy-pasted blocks that should be one shared implementation (DRY)

### 🔒 Security Issues

- SQL injection or string-interpolated queries instead of parameterized ones (OWASP injection prevention)
- Credentials, API keys, tokens, or secrets hardcoded or committed to the repo
- PII written to logs, error messages, or unencrypted/unmasked storage
- Overly permissive IAM roles, service accounts, or database grants (Principle of Least Privilege)
- Unvalidated or unsanitized inputs passed into downstream queries or systems
- Insecure connections — plain HTTP, skipped TLS verification, unencrypted transport
- Data leakage risk across tenant boundaries or between environments (prod/staging bleed)

### 🏗️ Architectural Issues

- Component tightly coupled to a specific external system, schema/API version, or tool with no abstraction layer (Dependency Inversion)
- Missing idempotency — re-running the operation produces duplicates or inconsistent results (Idempotent Receiver)
- Unbounded queries, scans, or loops that will silently degrade or fail at scale
- Blocking synchronous operations where async or parallel processing is warranted
- Schema/contract drift not handled — code assumes a fixed structure with no validation or contract test
- Observability gaps — no metrics, logs, or alerting hooks for a component expected to run unattended

---

## Review Text Style

Whoever reads this is triaging fast, not studying prose. Every Issue, Summary,  
and Verdict line follows these rules:

- Lead with what breaks or what to do — never scene-setting, never "Let's  
  look at...", never a recap of the diff.
- One idea per sentence. Max 20 words for an Issue cell, 25 for Summary/Verdict  
  prose.
- Active voice, common concrete words. Cut hedges that add no information  
  ("might", "could possibly", "seems to").
- No idioms ("circle back", "on the same page") — state the literal action.
- No preamble ("Great PR!") and no closing pleasantries ("let me know if...",  
  "hope this helps").
- Prefer a table over a bulleted list wherever the items are comparable in  
  shape — it scans faster than prose. Cap any list/table at 5 rows; beyond  
  that, keep the 5 most significant and drop the rest.

---

## Output Format

Produce the review in this exact structure. Do not omit any section, even if  
it has no findings — use "No issues found." in that case.

```markdown
### Summary
[1–2 sentences. What it does + merge-readiness. No elaboration.]

### 🔴 Pain Points
| # | Location | Issue | Severity |
|---|----------|-------|----------|
| 1 | file.py:42 | [One sentence: what breaks and why it matters.] | 🔴 Blocker |

Severity scale:
- 🔴 Blocker  — Must fix before merge. Risk of data loss, corruption, or production failure.
- 🟡 Major    — Should fix before merge. Significant tech debt, reliability, or correctness risk.
- 🟢 Minor    — Fix in a follow-up. Style, readability, or low-impact improvement.

### 🔒 Security Issues
| # | Location | Issue | Severity |
|---|----------|-------|----------|

### 🏗️ Architectural Issues
| # | Location | Issue | Severity |
|---|----------|-------|----------|

### ✅ What's Done Well
| # | Pattern |
|---|---------|
| 1 | [Name the pattern or decision — no elaboration. Max 5 rows.] |

### Verdict
**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**

[1–2 sentences. If REQUEST CHANGES, name the specific blockers. If NEEDS DISCUSSION,
name the open question that must be resolved first.]
```

---

## Severity Guidance

Use this to calibrate — don't over-block on style, don't under-block on correctness.

| Condition                                                            | Severity   |
| -------------------------------------------------------------------- | ---------- |
| Could cause data loss, duplication, or silent corruption             | 🔴 Blocker |
| Exposes credentials, PII, or creates an exploitable injection vector | 🔴 Blocker |
| Breaks an existing contract with no migration path                   | 🔴 Blocker |
| No error handling on a critical path that will eventually fail       | 🟡 Major   |
| Missing idempotency on a job that will be retried or backfilled      | 🟡 Major   |
| Hardcoded environment values that block multi-env deployment         | 🟡 Major   |
| No tests on non-trivial transformation logic                         | 🟡 Major   |
| Observability gap on a new pipeline with no existing monitoring      | 🟡 Major   |
| Inconsistent naming or minor style deviation                         | 🟢 Minor   |
| Logging that could be improved but isn't misleading                  | 🟢 Minor   |
| Minor inefficiency in a non-hot path                                 | 🟢 Minor   |

Domain-specific severities (Airflow, dbt, Spark, Terraform, Helm, ML, etc.)  
are tagged inline on their checklist bullets in the reference files.

---

## Tips for Better Reviews

- **Add context**: hot-path frequency, PII sensitivity, or what you're unsure  
about (e.g. "not sure this handles late arrivals") sharpens the review.
- **Include tests** alongside the diff to get test-quality coverage too.
- **For domain-specific reviews**, include what unlocks deeper context: dbt →  
`schema.yml` + upstream `ref()` models; Terraform → the affected  
`variables.tf`/state backend; ML → training config and eval metrics.
