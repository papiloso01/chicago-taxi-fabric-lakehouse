# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "0ebf4156-1e38-5ae5-a9f3-e9d642511a07",
# META       "default_lakehouse_name": "lh_chicago_taxi",
# META       "default_lakehouse_workspace_id": "00000000-0000-0000-0000-000000000000"
# META     },
# META     "environment": {
# META       "environmentId": "3764ffaa-ce58-56d1-a48f-eac036d6fda3",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# PARAMETERS CELL ********************

mode = "daily"  # daily, year or range
start = ""
end = ""
year = ""
page_size = "5000"
landing_root = "/lakehouse/default/Files/landing"
landing_run_id = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import json
from chicago_taxi_fabric.ingestion.windows import resolve_window
from chicago_taxi_fabric.ingestion.landing import ingest

window_start, window_end = resolve_window(mode, start, end, year)
# Optional Socrata app token: store it in Azure Key Vault and read it here, never in source.
report = ingest(landing_root, window_start, window_end, page_size=int(page_size), run_id=landing_run_id or None)
result = {key: report[key] for key in ["run_id", "status", "start", "end_exclusive", "extracted_rows"]}
print(json.dumps(result))
notebookutils.notebook.exit(json.dumps(result))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
