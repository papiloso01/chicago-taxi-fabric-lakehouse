import importlib.util
import json
import shutil
import pytest
import yaml
from chicago_taxi_fabric.naming import qualified, spark_path, table_name
from chicago_taxi_fabric.transformations.silver.contracts import SCHEMAS as SILVER
from chicago_taxi_fabric.transformations.gold.contracts import SCHEMAS as GOLD


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


metadata = load("tools/validate_metadata.py", "validate_metadata")
fabric = load("tools/validate_fabric_items.py", "validate_fabric_items")


def test_metadata_validates():
    assert metadata.validate() == 1


def test_fabric_items_validate():
    assert fabric.validate() == 7


@pytest.mark.parametrize("layer,schemas", [("silver", SILVER), ("gold", GOLD)])
def test_metadata_matches_code_contracts(layer, schemas):
    tables = yaml.safe_load(open(f"metadata/{layer}_tables.yml"))["tables"]
    assert {t["name"].split(".")[-1]: t["schema_sql"] for t in tables} == schemas


@pytest.mark.parametrize("defect", ["duplicate", "missing_key", "foreign_key", "wrong_schema"])
def test_bad_metadata_rejected(tmp_path, defect):
    shutil.copytree("metadata", tmp_path / "metadata")
    path = tmp_path / "metadata" / "silver_tables.yml"
    data = yaml.safe_load(path.read_text())
    if defect == "duplicate":
        data["tables"].append(data["tables"][0])
    elif defect == "missing_key":
        data["tables"][0]["key"] = "missing"
    elif defect == "foreign_key":
        data["foreign_keys"][0]["target"] = "dim_taxi.missing"
    else:
        data["tables"][0]["name"] = "lh_chicago_taxi.gold.fact_trip"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError):
        metadata.validate(tmp_path / "metadata")


def test_pipeline_with_unknown_notebook_rejected(tmp_path):
    shutil.copytree("fabric", tmp_path / "fabric")
    path = tmp_path / "fabric" / "pl_taxi_landing_to_gold.DataPipeline" / "pipeline-content.json"
    data = json.loads(path.read_text())
    data["properties"]["activities"][1]["typeProperties"]["notebookId"] = "missing"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="notebook"):
        fabric.validate(tmp_path / "fabric")


def test_identifiers_and_paths():
    assert qualified("lh_chicago_taxi", "bronze", "taxi_trips") == "lh_chicago_taxi.bronze.taxi_trips"
    with pytest.raises(ValueError):
        table_name("bronze.taxi_trips; DROP TABLE x")
    assert spark_path("/lakehouse/default/Files/landing/x") == "Files/landing/x"
    assert spark_path("/tmp/stage") == "file:///tmp/stage"
    with pytest.raises(ValueError):
        spark_path("relative/path")
