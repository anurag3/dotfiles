---
name: buyer-intent-seed-checks
description: Use when changes are made to buyer_intent seed files in seeds/buyer_intent/ — runs duplicate, scientific notation, and category validation checks on trust_radius CSV mapping files.
---

# Buyer Intent Seed Checks

## Overview

Validates trust_radius seed CSV files after changes. Three checks: duplicates, scientific notation in IDs, malformed category rows.

## When to Use

- After editing any file under `seeds/buyer_intent/`
- Before committing changes to trust_radius mapping seeds
- When reviewing a PR that touches buyer_intent seeds

## Steps

### 1. Check for changes

```bash
git diff --name-only origin/main seeds/buyer_intent/
git diff --cached --name-only seeds/buyer_intent/
```

Capture the output. If no files changed, report "No buyer_intent seed changes detected — skipping checks." and stop.

### 2. Duplicate rows check

```bash
sort seeds/buyer_intent/trust_radius_products_mapping.csv | uniq --count --repeated
sort seeds/buyer_intent/trust_radius_vendors_mapping.csv | uniq --count --repeated
```

**Pass:** No output. Any output = duplicate rows that must be removed.

### 3. Scientific notation check

```bash
grep -nE '[0-9]+\.?[0-9]*[E][+-]?[0-9]+' seeds/buyer_intent/trust_radius_products_mapping.csv
grep -nE '[0-9]+\.?[0-9]*[E][+-]?[0-9]+' seeds/buyer_intent/trust_radius_vendors_mapping.csv
```

**Pass:** No output. Any match = numeric ID stored in scientific notation (e.g. `1.23E+7`). Fix by expanding to full integer in the CSV.

### 4. Category mapping check

```bash
tail -n +2 seeds/buyer_intent/trust_radius_categories_mapping.csv | grep -vE ",(PIQ Code|Attribute ID),"
```

**Pass:** No output (all rows are header or valid mapped rows). Any output = rows missing expected column markers — investigate before committing.

## Reporting

After all checks, summarize:

```
Buyer intent seed checks:
- Duplicates (products): PASS / FAIL (N rows)
- Duplicates (vendors):  PASS / FAIL (N rows)
- Scientific notation (products): PASS / FAIL (lines: ...)
- Scientific notation (vendors):  PASS / FAIL (lines: ...)
- Categories:             PASS / FAIL (N unexpected rows)
```
