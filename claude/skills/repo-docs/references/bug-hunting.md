# Bug hunting

Use this checklist when you read code for `init`, `update`, or `audit`. Paste the "Checklist", "Evidence bar", and "Item format" sections into each general-purpose subagent brief.

## Checklist

Look for these latent-bug patterns in data pipelines and services. For each hit, record `path:line`, the effect, and the evidence.

| Pattern | What to check | Example |
|---|---|---|
| Swapped positional arguments or columns | An `INSERT` without a column list, or a call with positional arguments of the same type. Compare the order with the table DDL or the function signature | `insert into t select external_source, external_id` against DDL `(external_id, external_source)` |
| Config key that has no effect | A config key with a typo or a wrong prefix. The system ignores it with no error | `spark.shuffle.partitions` is not a key. The correct key is `spark.sql.shuffle.partitions` |
| Silent mock or fallback path | A missing credential, connection, or data source returns fake, empty, or default data, not an error | A missing API key returns `sample_results()`. The UI shows realistic numbers |
| Inner join that drops rows | An `inner join` to a lookup or seed with no test that the row count stays the same | Orders in a new currency drop from `fct_orders` |
| Case-sensitive exact join to a seed | A join on a string key with no `lower()` or `trim()`, to a hand-edited CSV | `'Acme Inc'` does not match `'ACME Inc'` |
| `LIMIT` with no order used to sample | Sampled tables joined to each other, or tests that depend on sampled rows | Two sampled tables share almost no keys |
| Null changed to a sentinel value | `coalesce(x, 0)`, `coalesce(x, '')`, or `-1`. Later code counts or joins on the sentinel | All unknown IDs join to one row with ID `0` |
| Non-deterministic value | `current_timestamp()`, `now()`, `uuid()`, or `rand()` in a key, a dedup, or a test | A rebuild changes keys, so downstream merges duplicate rows |
| Unused or dead config | A parameter, variable, or job argument that no code reads | A job declares table parameters that no task uses |
| Duplicate config keys combined by string concatenation | A config merge that appends values for the same key | `--conf a=1 --conf a=2` gives `a=12` |
| Credentials in a URL with no encoding | A user name or password put in a JDBC or HTTP URL as raw text | A password with `@` or `/` breaks the connection |
| Tests that never run or never fail | A test folder with no `__init__.py`, a wrong file name pattern, a generic test with a logic error, or a skip with no reason | A length test uses `and` where it must use `or`, so it never fails |
| Missing retries or alerts | A job, task, or external call with no retry, no timeout, and no failure alert | A nightly job fails and nobody gets a message |
| Wrong error handling | A broad `except` that logs and continues, or a return code that the caller ignores | A failed load writes 0 rows and the job passes |
| Missing import or name | A name that the file uses but does not define or import, often in notebooks | `timezone.utc` with no `from datetime import timezone` |
| Different constants for one value | The same ID or code with different values in different steps | `region_id = 4` in one step and `= 7` in the next step |

Also compare the code with `README.md`, `AGENTS.md`, `CLAUDE.md`, and code comments. Record each difference as Doc drift.

## Evidence bar

Use `Confirmed:` when one of these is true:

1. You read the code at `path:line` and traced the full path that causes the effect. You do not need to run it.
2. A test, a run, a log, or a query result shows the effect.
3. Official documentation for the library or system states the behavior. Cite the setting and the code line.

Use `Inferred:` when one of these is true:

1. The effect depends on data, configuration, or runtime state that you did not see.
2. You read only part of the path, for example a caller in another repo.
3. You concluded the behavior from names, comments, or patterns, not from the code that runs.

Do not lower a claim that meets the bar for `Confirmed:` to `Inferred:` to be safe. A traced bug marked as "probable" is an error. Write what is not checked in the evidence part, for example "No run checked the row count."

Do not run a command against a live system (Databricks, a warehouse, Airflow, a network service) to get evidence without the user's approval.

## Item format

Each bug in `known-issues.md` has this form:

```markdown
- Confirmed: `path/to/file.py:88` <one-sentence claim>. Effect: <what goes wrong, for whom>. Evidence: <the code, test, or doc that shows it, with `path:line`>.
```

Put the item in the section that matches its marker: "Confirmed bugs" or "Inferred bugs". Put contradictions between repo docs and code in "Doc drift". When a commit fixes a bug, move the item to "Resolved" and add the fixing SHA and date.
