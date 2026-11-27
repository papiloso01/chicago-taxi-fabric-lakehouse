Review changes against docs/architecture.md and docs/roadmap.md. This is a foundation; Fabric
acceptance runs are manual and recorded in the roadmap, not proven by CI.
Preserve Chicago end-exclusive dates, trip_id keyset pagination, source-key replay (MERGE), trip
grain and revenue reconciliation. Bronze consumes only explicit runs with a success manifest.
Use lakehouse.schema.table identifiers for the schema-enabled lakehouse; Spark reads OneLake files
via Files/ or abfss paths, Python file APIs via /lakehouse/default/Files.
Do not infer driver identities or passenger gender. Retain unknown geography as area_key 0.
No credentials in source (use Key Vault); no workspace, capacity or schedule changes from CI.
