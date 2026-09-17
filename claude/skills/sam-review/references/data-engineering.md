# Data Engineering Traps

Domain-specific bullets to layer onto the core Pain Points / Architectural
checklist when the diff touches pipelines, ETL/ELT, dbt, Spark, Airflow, SQL,
or schema/warehouse changes.

## Pain Points

- **DE-specific traps** *(🟡 Major)*: timezone assumptions (naive datetime vs. UTC-aware, `data_interval_end` misuse), NULL semantics silently changing row counts in aggregations or joins, partition skew causing hotspots or OOM
- **Airflow traps** *(🟡 Major)*: tasks with no `retries`/`retry_delay` on flaky operators, sensors left in default poke mode with no `timeout` (blocks a worker slot indefinitely), `execution_date` used instead of `data_interval_start`/`data_interval_end`, XCom used to pass bulk data instead of a pointer/reference
- **dbt traps** *(🔴 Blocker if duplicating)*: incremental models with no `unique_key` (or a merge strategy that still allows duplicates) causing row duplication on re-run, `{{ this }}` referenced without an incremental guard
- **Spark traps:** driver-side `.collect()`/`.toPandas()` on data that won't reliably fit in driver memory, row-wise `.apply()`/Python UDFs used where a native or vectorized function would do
- **Premature optimization (Spark)** *(🟢 Minor; 🟡 Major if it obscures a bug)*: manual repartitioning, `cache()`/`persist()`, custom serializers, or RDD-level tuning added for a performance concern that hasn't been measured — adds complexity and maintenance cost against an unproven need; profile the actual bottleneck first

## Architectural Issues

- No backfill strategy or late-arrival handling for event-time or time-series data
- No data quality checks or assertions at key transformation or load steps
- Observability gaps specific to pipelines: no lineage tracking, no row-count or freshness metrics on output
- **Cost at scale** *(🟡 Major)*: unbounded scans with no partition pruning, oversized clusters for the actual workload, small-file explosion amplifying S3/storage request costs — ask "what does this bill at 10x volume?"
- **Operational readiness** *(🔴 Blocker)*: failure leaves data in a partial or inconsistent state with no safe re-trigger path; no documented recovery steps for likely failure modes; on-call burden increases with no mitigation
- **Downstream contract impact** *(🟡 Major)*: output schema, column names, file paths, or partition structure consumed by other pipelines, models, or reports changed without auditing consumers — one-line changes cascade silently
- **Numeric precision / type narrowing** *(🟡 Major)*: decimal-to-double or double-to-decimal conversions, narrowing casts (`bigint`→`int`, `double`→`float`), or precision/scale changes on an existing decimal column — can silently truncate or lose precision in downstream aggregations
- **Medallion/layering violations** *(🟡 Major)*: raw or landing data written directly to a gold/serving table with no bronze/silver validation or dedup step in between; a mart model querying `source()` directly instead of going through a staging layer
- **Databricks-specific** *(🔴 Blocker if history-destroying)*: Delta table written with `overwrite` where a `merge`/upsert was needed (destroys history on rerun), no `OPTIMIZE`/Z-ORDER or compaction plan for a table that will accumulate small files, schema evolution (Auto Loader/`mergeSchema`) not handled — schema drift breaks the pipeline silently
- **`spark_version`/cluster-config drift** *(🟡 Major)*: a bundle's `databricks.yml` or job/pipeline cluster spec has a DBR (`spark_version`), node type, autoscale bounds, or library set that diverges across dev/staging/prod targets with no stated reason, or pins an EOL/soon-to-EOL runtime
- **Spark scale traps:** wide shuffle (join/groupBy) on skewed keys with no repartitioning, join against a small dimension table with no broadcast hint

## ML-Specific Traps

- **Train/test leakage** *(🔴 Blocker)*: feature computed using information not available at prediction time (future data, target-derived aggregates, leakage through a shared preprocessing step fit on the full dataset instead of train-only)
- **Reproducibility** *(🟡 Major)*: training run with no fixed seed, no pinned library/data versions, or no logged config — the same run can't be reproduced or audited later
- **Model/artifact versioning** *(🟡 Major)*: no clear mapping from a deployed model artifact back to the training run/commit/data snapshot that produced it
- **Evaluation traps** *(🟡 Major)*: metric doesn't match the actual business objective (e.g. accuracy on an imbalanced class), no comparison against the current production baseline before promoting a new model
- **Online/offline skew** *(🔴 Blocker if silent)*: feature computed differently at training time vs. serving time (different code path, different data source), producing predictions that silently degrade in production
- **Training data handling** *(🔴 Blocker if PII)*: PII or sensitive fields present in training data or logged eval artifacts without anonymization/masking
