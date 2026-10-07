---
name: sampling-databricks-tables
description: >
  Confirms a Unity Catalog table's real columns, sample rows, and size with discover-schema or
  DESCRIBE DETAIL before running non-trivial SQL, and uses LEFT JOIN for match-rate checks. Use
  before any aggregation, join, CASE WHEN rollup, or query without LIMIT against a Databricks table
  whose columns were not confirmed in this session.
---

# Sampling Databricks Tables

Before you run non-trivial SQL against a Unity Catalog table, confirm the real structure and approximate size of the table in the same session. Non-trivial SQL includes aggregations, multi-column `CASE WHEN` rollups, joins, and queries without a `LIMIT`. Do not guess column names from memory or from naming conventions.

Each command in this skill runs against a live workspace. Get user approval before you run it (CLAUDE.md rule 9).

## Procedure

1. Run `databricks experimental aitools tools discover-schema <catalog.schema.table> --profile <PROFILE>`. One call returns the real column names and types, 5 sample rows, null counts, and the total row count.
   - If `discover-schema` is not available, run `DESCRIBE TABLE <table>` and `SELECT * FROM <table> LIMIT 10` instead.
2. For file and storage size (`numFiles`, `sizeInBytes`), run `DESCRIBE DETAIL <table>`. `discover-schema` does not return these values.
   - Do not use `COUNT(*)` for size. On a plain Delta table with no filter, `COUNT(*)` reads only metadata. On views, external or non-Delta tables, and streaming tables, `COUNT(*)` does a full scan.
3. Write the full aggregation or join query only after steps 1 and 2.
4. To measure match rates or coverage between two datasets or tables, use `LEFT JOIN` and count the non-null matches. Do not use `INNER JOIN`. An `INNER JOIN` drops each row that does not match, so the result always shows a 100% match, whatever the real coverage.

## When to skip

Skip this procedure only when you confirmed the columns earlier in the same session.

## Genie One

Prefer Genie One (`databricks genie ask`) for general data questions. Genie One finds the schema and joins itself, so this type of mistake does not occur.
