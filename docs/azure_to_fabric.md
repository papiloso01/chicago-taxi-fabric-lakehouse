# Mapping from chicago-taxi-azure-lakehouse

| Azure repo | This repo (Fabric) |
|---|---|
| Azure Data Factory pipeline `pl_taxi_landing_bronze_silver_gold` | Fabric Data Pipeline `pl_taxi_landing_to_gold` |
| `DatabricksJob` activities invoking saved serverless jobs | `TridentNotebook` activities invoking workspace notebooks |
| Databricks notebooks + wheel on job environment | Fabric notebooks + wheel on the `env_chicago_taxi` Environment |
| ADLS Gen2 + Unity Catalog volume `/Volumes/.../landing` | OneLake lakehouse `Files/landing` |
| Unity Catalog `catalog.schema.table` | Schema-enabled lakehouse `lakehouse.schema.table` |
| `dbutils.widgets` / `dbutils.notebook.exit` | Parameters cell / `notebookutils.notebook.exit` |
| Linked services and managed identities | Workspace identity and lakehouse default attachment |
| MySQL serving (blocked) + Tableau | Direct Lake semantic model + Power BI (planned) |

Data rules, windows, manifest checks, bronze MERGE, silver contracts and reconciliation follow the
Azure repo. Community-area names, map boundaries and the full set of gold marts are not ported yet;
see the roadmap.
