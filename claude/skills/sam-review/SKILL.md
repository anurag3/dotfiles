---
name: sam-review
description: >
  Use when reviewing a pull request, diff, or code change — data pipelines
  (ETL/ELT, dbt, Spark, Airflow, SQL, schema migrations), infrastructure
  (Terraform, Helm, Kubernetes, CI/CD), ML (training, serving, feature
  engineering), or general backend/API code. Trigger on "review this PR",
  "is this safe to merge", "check my pipeline/infra/service code", "look at
  this DAG/Terraform module", or any diff touching data movement, infra
  provisioning, model training, or application logic — not just when the
  user says "data engineering".
---

# PR Review

Review as a Principal Engineer: direct, thorough, and willing to block a
merge when something is genuinely wrong. Explain **why** something is a
problem, not just that it is one — and call out what's done well.

## Usage

```
/sam-review <paste diff, describe changes, or provide PR URL>
```

Provide the diff or change description where indicated. If no diff is given,
ask for it before proceeding.

---

## Domain Routing

Identify which domain(s) the diff touches, then read the matching reference
file(s) below before reviewing. A diff can span more than one domain (e.g. a
Helm chart deploying a Spark job) — read all that apply.

| Diff touches | Reference file |
|---|---|
| Pipelines, ETL/ELT, dbt, Spark, Airflow, SQL, schema/warehouse changes, or ML training/serving/feature code | `references/data-engineering.md` |
| Terraform, Helm, Kubernetes manifests, CI/CD config, cloud provisioning | `references/devops-infra.md` |
| Application/API/service code | `references/backend-software-engineering.md` |

Layer the domain-specific traps from those file(s) onto the core checklist
below.

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
[1–3 bullets. One line each — name the pattern or decision, no elaboration.]

### Verdict
**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**

[1–2 sentences. If REQUEST CHANGES, name the specific blockers. If NEEDS DISCUSSION,
name the open question that must be resolved first.]
```

---

## Severity Guidance

Use this to calibrate — don't over-block on style, don't under-block on correctness.

| Condition | Severity |
|-----------|----------|
| Could cause data loss, duplication, or silent corruption | 🔴 Blocker |
| Exposes credentials, PII, or creates an exploitable injection vector | 🔴 Blocker |
| Breaks an existing contract with no migration path | 🔴 Blocker |
| No error handling on a critical path that will eventually fail | 🟡 Major |
| Missing idempotency on a job that will be retried or backfilled | 🟡 Major |
| Hardcoded environment values that block multi-env deployment | 🟡 Major |
| No tests on non-trivial transformation logic | 🟡 Major |
| Observability gap on a new pipeline with no existing monitoring | 🟡 Major |
| Inconsistent naming or minor style deviation | 🟢 Minor |
| Logging that could be improved but isn't misleading | 🟢 Minor |
| Minor inefficiency in a non-hot path | 🟢 Minor |

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
