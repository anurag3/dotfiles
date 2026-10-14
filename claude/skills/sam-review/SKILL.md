---
name: sam-review
description: >
  Reviews code changes as a Principal Engineer and produces a severity-ranked
  report of pain points, security issues, and architectural issues, with a
  merge verdict. Covers data pipelines (ETL/ELT, dbt, Spark, Airflow, SQL,
  schema migrations), infrastructure (Terraform, Helm, Kubernetes, CI/CD), ML,
  and backend/API code. Use when the user asks to review a pull request (e.g.
  "review this PR <link>", "is this PR safe to merge <link>") or a local diff
  or branch (e.g. "review this diff", "review my branch"), and when a reviewer
  agent is dispatched to review code.
---

# Code Review

Review as a Principal Engineer: direct, thorough, and willing to block a  
merge when something is genuinely wrong. Explain **why** something is a  
problem, not just that it is one, and call out what's done well.

## Fetch the Diff

Fetch the diff yourself before reviewing.

**PR URL given** (works from any directory: `gh` resolves the repo from the URL):

```bash
gh pr view <PR URL> --json title,body,files,additions,deletions,commits
gh pr diff <PR URL> --patch > /tmp/pr<number>.diff
```

The PR's branch is usually not checked out locally. The working tree is most often
on the base branch (e.g. `develop`/`main`), which may lack the file entirely or hold
an older version of it. Derive every `Location` (`file.py:42`) citation from the diff
file's own hunk headers (`@@ -a,b +c,d @@`), not from grepping or reading the file in
the local working tree. That's the same local-checkout trap the Large Diff Fan-Out
Protocol guards sub-agents against, and it applies just as much to a direct review.
Only read local files to pull in context the diff itself doesn't show (e.g. an
unchanged helper the diff calls into), and even then, confirm via the diff that the
surrounding code is unchanged before trusting the local version's line numbers.

**No PR URL (local diff or branch):**

```bash
git diff > /tmp/review-local.diff                            # uncommitted changes
git diff <base-branch>...<branch-name> > /tmp/review-local.diff  # branch vs. its base
```

Here the working tree usually *is* the branch under review, so reading the local file
directly for context is safe. Confirm with `git status`/`git branch --show-current`
which branch you're actually on first. The diff-file line-number trap below still
applies whenever you cite a `Location` from the `.diff` file itself.

**Common failure mode:** when you `Read` the `.diff` file, the tool prefixes every line
with its own line number *within that diff file* (patch email headers, `From ...`,
`Subject ...`, `diff --git`, `index ...` lines all count). That prefix is NOT the target
file's line number. It's just where the line sits in the patch text. Never cite a
`Location` using those prefixes. The only valid inputs to a line-number calculation are:
1. The hunk header's own starting line (`@@ -a,b +c,d @@` → the target line is `c` for
   the new file, `a` for a deleted line).
2. A manual count of hunk lines from that starting point: count every ` ` (context) and
   `+` (added) line as one line of the new file; skip `-` (removed) lines entirely; skip
   the hunk header line itself.
For a deletion-only finding, count against the *old* file using `a` and the `-`/` ` lines
instead. If a hunk spans more than ~10 lines, count out loud (list each new-file line
number next to its content) rather than eyeballing it. This is the step that produced
wrong line numbers before.

---

## Domain Routing

Identify which domain(s) the diff touches, then read the matching reference  
file(s) below before reviewing. A diff can span more than one domain (e.g. a  
Helm chart deploying a Spark job). Read all that apply.

| Diff touches                                                                                                | Reference file                               |
| ----------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Pipelines, ETL/ELT, dbt, Spark, Airflow, SQL, schema/warehouse changes, or ML training/serving/feature code | `references/data-engineering.md`             |
| Terraform, Helm, Kubernetes manifests, CI/CD config, cloud provisioning                                     | `references/devops-infra.md`                 |
| Application/API/service code                                                                                | `references/backend-software-engineering.md` |

Layer the domain-specific traps from those file(s) onto the core checklist  
below.

**Large Diff Fan-Out Protocol:** fan out to sub-agents only for a large diff (rule of thumb:  
more than 500 changed lines, or files across more than two domains). Review other diffs directly.  
Read `references/fan-out.md` and follow it.

---

## Review Checklist

Work through all three areas for every review. Do not skip a category because  
the diff looks small. Subtle issues often hide in small changes.

### 🔴 Pain Points (Obvious Issues)

- Logic errors, off-by-one mistakes, silent failures
- Missing error handling or no retry logic on flaky operations
- Hardcoded values that should be config- or environment-driven (12-Factor config)
- Missing, misleading, or excessively noisy logging
- Tests that are absent, trivial, or structured in a way that can't catch regressions
- Breaking changes to contracts (schema, API, file format, column names) with no migration plan
- Functions or tasks doing too much: no clear single responsibility (SRP)
- **Speculative generality** *(🟢 Minor)*: config knobs, flags, or abstraction layers built for a hypothetical future need with no current caller (YAGNI)
- **Needless complexity** *(🟢 Minor; 🟡 Major if it obscures a correctness issue)*: extra layers, indirection, or cleverness for a problem a simpler approach would solve (KISS)
- **Duplicated logic** *(🟢 Minor; 🟡 Major if copies have already drifted)*: copy-pasted blocks that should be one shared implementation (DRY)

### 🔒 Security Issues

- SQL injection or string-interpolated queries instead of parameterized ones (OWASP injection prevention)
- Credentials, API keys, tokens, or secrets hardcoded or committed to the repo
- PII written to logs, error messages, or unencrypted/unmasked storage
- Overly permissive IAM roles, service accounts, or database grants (Principle of Least Privilege)
- Unvalidated or unsanitized inputs passed into downstream queries or systems
- Insecure connections: plain HTTP, skipped TLS verification, unencrypted transport
- Data leakage risk across tenant boundaries or between environments (prod/staging bleed)

### 🏗️ Architectural Issues

- Component tightly coupled to a specific external system, schema/API version, or tool with no abstraction layer (Dependency Inversion)
- Missing idempotency: re-running the operation produces duplicates or inconsistent results (Idempotent Receiver)
- Unbounded queries, scans, or loops that will silently degrade or fail at scale
- Blocking synchronous operations where async or parallel processing is warranted
- Schema/contract drift not handled: code assumes a fixed structure with no validation or contract test
- Observability gaps: no metrics, logs, or alerting hooks for a component expected to run unattended

---

## Review Text Style

Whoever reads this is triaging fast, not studying prose. Every Issue, Summary,  
and Verdict line follows these rules:

- Lead with what breaks or what to do, never scene-setting, never "Let's  
  look at...", never a recap of the diff.
- One idea per sentence. Max 20 words for an Issue cell, 25 for Summary/Verdict  
  prose.
- Active voice, common concrete words. Cut hedges that add no information  
  ("might", "could possibly", "seems to").
- No idioms ("circle back", "on the same page"). State the literal action.
- No preamble ("Great PR!") and no closing pleasantries ("let me know if...",  
  "hope this helps").
- Prefer a table over a bulleted list wherever the items are comparable in  
  shape. It scans faster than prose. Cap any list/table at 5 rows; beyond  
  that, keep the 5 most significant and drop the rest.

---

## Output Format

Produce the review in this exact structure. Do not omit any section, even if  
it has no findings. Use "No issues found." in that case.

````markdown
### Summary
[1–2 sentences. What it does + merge-readiness. No elaboration.]

### 🔴 Pain Points
| # | Location | Issue | Severity |
|---|----------|-------|----------|
| 1 | file.py:42 | [One sentence: what breaks and why it matters.] | 🔴 Blocker |

**#1 · `file.py:40-42`**

blocker: [What breaks and why. The ask.]

```suggestion
[Replacement lines, indented exactly as in the file.]
```

Severity scale:
- 🔴 Blocker: Must fix before merge. Risk of data loss, corruption, or production failure.
- 🟡 Major: Should fix before merge. Significant tech debt, reliability, or correctness risk.
- 🟢 Minor: Fix in a follow-up. Style, readability, or low-impact improvement.

### 🔒 Security Issues
| # | Location | Issue | Severity |
|---|----------|-------|----------|

### 🏗️ Architectural Issues
| # | Location | Issue | Severity |
|---|----------|-------|----------|

### ✅ What's Done Well
| # | Pattern |
|---|---------|
| 1 | [Name the pattern or decision. No elaboration. Max 5 rows.] |

### Verdict
**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**

[1–2 sentences. If REQUEST CHANGES, name the specific blockers. If NEEDS DISCUSSION,
name the open question that must be resolved first.]
````

The Security Issues and Architectural Issues tables use the same pattern:  
the table, then one comment block for each row. A table with "No issues  
found." has no comment blocks.

During fan-out reconciliation, suffix `Issue` with ` (unverified)` for a  
finding you passed through without independently confirming it against the  
diff text. Put the suffix on the finding row's `Issue` cell. The comment for  
that finding uses the `question:` label. Leave every other row unsuffixed.

---

## PR Comments

Under each finding table, write one comment block for each row, in row  
order. The user pastes each comment on the PR without changes. Do not put a  
comment in a table cell.

Write each comment block in this order:

1. Heading: ``**#<n> · `<Location>`**``. `<n>` is the row number in that  
   table. `<Location>` is the exact line range that the comment attaches to  
   and that a suggestion replaces.
2. A blank line.
3. The comment line: `<label>: <what breaks and why>. <the ask>.` Write it as  
   plain text on one line, not in a table cell or a wrapped paragraph. Use 30  
   words or fewer. Write the ask as a request ("Can we ...?") or as a direct  
   instruction.
4. If the `suggestion` block rules permit it, a `suggestion` block.

You can also write praise comments. Write a praise comment only for a ✅  
What's Done Well row that is unusually good. Examples are a pattern that the  
team can use again and a good decision that is not obvious. Most reviews need  
zero or one praise comment. Do not write a praise comment for standard good  
practice. Put each praise comment block directly under the ✅ What's Done  
Well table. Use ``**#<n> · `<Location>`**`` as the heading, then a blank line,  
then the praise line. Set the Location to the lines in the diff that show the  
pattern.

- Praise comment line: `<label>: <what is good and why>.` Write one line of 30  
  words or fewer. Do not write an ask.

| Finding                                                                    | Label            |
| -------------------------------------------------------------------------- | ---------------- |
| 🔴 Blocker                                                                 | `blocker:`       |
| 🟡 Major                                                                   | `issue:`         |
| 🟢 Minor                                                                   | `suggestion:`    |
| 🟢 Minor, naming or style only                                             | `nit:`           |
| Any severity, marked `(unverified)` or dependent on facts outside the diff | `question:`      |
| ✅ What's Done Well: a pattern worth reusing in other code                 | `stealing this:` |
| ✅ What's Done Well: a good design decision                                | `love this:`     |
| ✅ What's Done Well: a fact or technique that is new to the reviewer       | `TIL:`           |
| ✅ What's Done Well: simple, readable code                                 | `clean:`         |

Use these rules for the `suggestion` block:

1. Add a `suggestion` block only when the fix replaces lines that the diff  
   shows in the new file. Otherwise, do not add the block.
2. Set the comment block heading Location to the exact line range that the  
   block replaces (`file.py:270-276`). GitHub replaces all lines in that range  
   with the block contents.
3. Copy the indentation of each line exactly from the diff. If the  
   indentation is wrong, the code breaks when the author commits the  
   suggestion.
4. Put only the replacement lines in the block. Do not include `+` or `-`  
   markers or `...` placeholders.
5. If the fix changes more than one file or lines outside the diff hunks, do  
   not add the block. GitHub cannot attach a suggestion to those lines.

---

## Severity Guidance

Use this to calibrate: don't over-block on style, don't under-block on correctness.

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
