"""Offline end-to-end: fixture API -> landing manifest -> staged JSON -> bronze -> silver -> gold."""
import pytest
from tests.spark_session import spark  # noqa: F401
from tests.conftest import fake_api, trip

pytest.importorskip("pyspark")
from chicago_taxi_fabric.ingestion.landing import ingest
from chicago_taxi_fabric.naming import spark_path
from chicago_taxi_fabric.transformations.bronze.landing_manifest import stage_run
from chicago_taxi_fabric.transformations.bronze.taxi_trips import prepare, stage_schema
from chicago_taxi_fabric.transformations.silver.taxi_trips import build_tables, validate_tables
from chicago_taxi_fabric.transformations.gold.taxi_marts import build_marts, validate_marts


def test_landing_to_gold(tmp_path, spark):
    rows = [trip(f"t{i:02d}") for i in range(6)] + [trip("bad", trip_miles="oops")]
    report = ingest(tmp_path / "landing", "2025-01-01", "2025-01-02", page_size=3, fetch=fake_api(rows))
    manifest, stage = stage_run(tmp_path / "landing" / "taxi_trips" / ("run_id=" + report["run_id"]), tmp_path / "stage")
    source = spark.read.schema(stage_schema()).json(spark_path(stage))
    assert source.count() == manifest["extracted_rows"] == 7
    bronze = prepare(source)
    tables = build_tables(bronze)
    assert validate_tables(tables, bronze.count()) == dict(input_rows=7, fact_rows=6, quarantined_rows=1)
    marts = build_marts(tables, "e" * 32)
    summary = validate_marts(marts, tables["fact_trip"])
    assert summary == dict(trip_rows=6, known_revenue_usd="88.50")
