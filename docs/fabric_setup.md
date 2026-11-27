# Fabric setup

These steps are manual and done by the project owner. Nothing in this repository creates
capacity, workspaces or schedules.

1. **Capacity and workspace.** Create a workspace (for example `ws-chicago-taxi-dev`) on a Fabric
   or trial capacity.
2. **Git integration.** Workspace settings → Git integration → GitHub → this repository, branch
   `main`, Git folder `fabric`. Sync to create the lakehouse, environment, notebooks and pipeline.
3. **Check item bindings.** The notebooks and pipeline reference the lakehouse, environment and
   notebooks by the `logicalId` values in each `.platform` file, with the zero GUID meaning "this
   workspace". After the first sync, open each notebook and the pipeline and confirm the default
   lakehouse, environment and notebook references resolve; re-select them if Fabric shows them as
   missing, then commit from the workspace so Git records the bound values.
4. **Lakehouse schemas.** `lh_chicago_taxi` is schema-enabled. The notebooks create `bronze`,
   `silver` and `gold` schemas on first run.
5. **Environment wheel.** Build the wheel (`python -m build --wheel`, or download the
   `fabric-environment-wheel` CI artifact). Open `env_chicago_taxi` → Custom libraries → upload
   `chicago_taxi_fabric_lakehouse-<version>-py3-none-any.whl` → Publish. Republish after every
   package version change.
6. **Optional API token.** Store a Socrata app token in Azure Key Vault and read it in the ingestion
   notebook with `notebookutils.credentials.getSecret(...)`. Never commit it.
7. **First run.** Run `pl_taxi_landing_to_gold` manually with `mode=range`, `start=2025-01-01`,
   `end=2025-01-08`. Check each activity's exit JSON: landing `extracted_rows` equals bronze
   `extracted_rows`; silver `fact_rows + quarantined_rows` equals `input_rows`; gold `trip_rows`
   equals silver `fact_rows`.
8. **Replay check.** Re-run the bronze notebook alone with the same `landing_run_id`. Row counts
   in `bronze.taxi_trips` must not change.

Add a schedule only after these checks pass, and record the results in `docs/roadmap.md`.

## Pipeline parameters

| Parameter | Default | Meaning |
|---|---|---|
| `mode` | `daily` | `daily` (Chicago T−1), `year` (completed calendar year) or `range` |
| `start`, `end` | empty | ISO dates for `range` mode; `end` is exclusive |
| `year` | empty | Year for `year` mode |
| `page_size` | `5000` | Socrata page size (1–50000) |
| `landing_root` | `/lakehouse/default/Files/landing` | Notebook mount path for landing files |
| `lakehouse` | `lh_chicago_taxi` | Lakehouse name used in `lakehouse.schema.table` |
