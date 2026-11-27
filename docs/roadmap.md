# Implementation roadmap

## In this foundation

- Taxi API → OneLake landing with immutable run folders and success manifests.
- Bronze MERGE with manifest verification and replay safety.
- Silver typed fact, dimensions and quarantine with reconciliation and key checks.
- Gold daily summary, area demand and company/payment marts with coverage and reconciliation.
- Fabric lakehouse, environment, four notebooks and the four-stage pipeline in Git format.
- Offline functional, HTTP integration, Spark ETL validation and end-to-end CI suites.

## Pending live acceptance

1. Connect the workspace to Git and confirm item bindings ([setup](fabric_setup.md)).
2. Publish the wheel to the environment and run a one-week range end to end.
3. Replay bronze and rebuild silver/gold; confirm counts and revenue are unchanged.

## Remaining

1. Direct Lake semantic model and Power BI report over the gold schema.
2. Community-area names and map boundaries (port from the Azure repo).
3. Taxi revenue ranking and distance-extreme marts (port from the Azure repo).
4. Weather ingestion with source delay and missing-data coverage.
5. Daily schedule, late-arrival overlap, alerts and retry policy.
6. Deployment pipelines (dev → test → prod) or `fabric-cicd` for promotion.
7. Year backfill and runtime benchmarking; incremental silver/gold.
