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

landing_root = "/lakehouse/default/Files/landing"
landing_run_id = ""
lakehouse = "lh_chicago_taxi"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import json
from chicago_taxi_fabric.ingestion.landing import run_identity
from chicago_taxi_fabric.transformations.bronze.taxi_trips import load_run

if not landing_run_id:
    raise ValueError("landing_run_id is required: bronze only loads an explicit successful run")
run_path = f"{landing_root}/taxi_trips/run_id={run_identity(landing_run_id)}"
result = load_run(spark, run_path, lakehouse)
print(json.dumps(result))
notebookutils.notebook.exit(json.dumps(result))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
