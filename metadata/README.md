# Metadata

Versioned source definitions, reporting rules and per-layer table contracts. These are definitions,
not evidence of executed Fabric runs.

- `sources.yml`: endpoints, natural keys, time zones and window semantics.
- `reporting.yml`: metric rules every mart and report must respect.
- `silver_tables.yml` / `gold_tables.yml`: grain, keys, explicit schemas and foreign keys. They must
  match `src/chicago_taxi_fabric/transformations/*/contracts.py`; a functional test enforces that.

`python tools/validate_metadata.py` checks source, key and reference integrity.
