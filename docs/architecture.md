# Architecture decisions

**Orchestration.** The Fabric Data Pipeline `pl_taxi_landing_to_gold` owns parameters, date
modes and the order of the four notebook activities. Each stage runs only after the previous one
succeeds. The pipeline run ID (a GUID, normalised to 32 hex characters) is the landing run identity
shared by ingestion and bronze, so one pipeline run maps to exactly one landing folder.

**Compute.** Fabric Spark notebooks (Runtime 1.3, Spark 3.5, Delta 3.2) are thin entry points.
All logic lives in the `chicago_taxi_fabric` wheel, attached through the `env_chicago_taxi`
Environment, so it is unit-tested offline and versioned like the Azure repo's package.

**Storage.** One schema-enabled lakehouse, `lh_chicago_taxi`:

| Area | Contents |
|---|---|
| `Files/landing/taxi_trips/run_id=<id>/` | Immutable API pages, `audit.json`, and `manifest.json` only on success |
| `bronze` schema | `taxi_trips` (raw payload + extracted fields, MERGE on `trip_id`), `landing_runs` audit |
| `silver` schema | `fact_trip`, `dim_*`, `quarantine_trip`, `warehouse_loads` audit |
| `gold` schema | `mart_daily_summary`, `mart_area_demand_daily`, `mart_company_payment_daily`, `mart_loads` audit |

Tables are addressed as `lakehouse.schema.table`. Python file APIs use the notebook mount
`/lakehouse/default/Files/...`; Spark reads the same files through the relative `Files/...` path.

**Loading rules (unchanged from the Azure repo).**
- Windows are Chicago-local, inclusive start and exclusive end. Daily mode loads T−1.
- Bronze reads only a named run with a success manifest, re-verifies file hashes and row counts,
  rejects conflicting payloads for one trip and merges idempotently, so replay is safe.
- Silver rebuilds a full snapshot from one pinned bronze Delta version, types values, quarantines
  invalid rows and proves fact + quarantine = bronze and no orphan keys.
- Gold rebuilds from one pinned silver fact version and reconciles trip counts and revenue to silver.
- Each table write is atomic, but a layer is not one transaction. Block report refresh during a
  rebuild; a rerun repairs a partial failure.

**Serving.** A Direct Lake semantic model over the gold schema replaces the MySQL + Tableau path
of the Azure repo; it is planned, not yet in this repository.

**Testing.** CI uses offline fixtures only. Live acceptance in a Fabric workspace is a manual,
recorded step after merge.
