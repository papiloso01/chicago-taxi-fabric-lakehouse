"""Bronze, silver and gold DataFrame logic on local PySpark (no Delta or Fabric needed)."""
import json
from datetime import datetime
from decimal import Decimal
import pytest
from tests.spark_session import spark  # noqa: F401
from tests.conftest import trip

pytest.importorskip("pyspark")
from chicago_taxi_fabric.transformations.bronze.taxi_trips import prepare, stage_schema, merge_sql
from chicago_taxi_fabric.transformations.silver.taxi_trips import build_tables, validate_tables
from chicago_taxi_fabric.transformations.gold.taxi_marts import build_marts, validate_marts


def staged(spark, rows, run="a" * 32, file="start=2025-01-01/part-000000.json"):
    data = []
    for row in rows:
        payload = json.dumps(row, sort_keys=True)
        data.append((row.get("trip_id"), payload, str(hash(payload)), run, file, "2025-01-02T00:00:00+00:00"))
    return spark.createDataFrame(data, stage_schema())


def test_bronze_extracts_fields_and_drops_identical_duplicates(spark):
    rows = [trip("a"), trip("a"), trip("b")]
    df = prepare(staged(spark, rows))
    assert df.count() == 2
    assert df.filter("trip_id = 'a'").first().trip_total == "14.75"


def test_bronze_rejects_conflicting_payloads(spark):
    with pytest.raises(ValueError, match="Conflicting"):
        prepare(staged(spark, [trip("a"), trip("a", fare="1.00")]))


def test_bronze_rejects_missing_key(spark):
    with pytest.raises(ValueError, match="Missing trip key"):
        prepare(staged(spark, [{**trip("x"), "trip_id": None}]))


def test_merge_sql_validates_names():
    with pytest.raises(ValueError):
        merge_sql("taxi_trips", "bronze_stage_" + "0" * 32)
    with pytest.raises(ValueError):
        merge_sql("lh.bronze.taxi_trips", "x; DROP")


def silver(spark, rows):
    return build_tables(prepare(staged(spark, rows)))


def test_silver_types_local_time_and_unknowns(spark):
    tables = silver(spark, [trip("a"), trip("b", taxi_id=None, trip_total=None, trip_miles=None,
                                          pickup_community_area=None, company="  yellow   cab ")])
    rows = {row.trip_id: row for row in tables["fact_trip"].collect()}
    assert rows["a"].trip_km == Decimal("4.023360") and rows["a"].trip_total == Decimal("14.75")
    assert rows["a"].trip_start_local == datetime(2025, 1, 1, 1) and rows["a"].start_date_key == 20250101
    assert rows["b"].trip_total is None and not rows["b"].has_trip_total and rows["b"].pickup_area_key == 0
    assert dict(tables["fact_trip"].dtypes)["trip_start_local"] == "timestamp_ntz"
    assert tables["dim_company"].count() == 1  # normalised to one member
    assert validate_tables(tables, 2) == dict(input_rows=2, fact_rows=2, quarantined_rows=0)


@pytest.mark.parametrize("changes,issue", [
    ({"trip_miles": "bad"}, "invalid_trip_miles"),
    ({"trip_total": "-1"}, "invalid_trip_total"),
    ({"pickup_community_area": "78"}, "invalid_pickup_community_area"),
    ({"trip_start_timestamp": "2025/01/01"}, "invalid_trip_start_timestamp"),
    ({"trip_end_timestamp": "2025-01-01T00:00:00.000"}, "end_before_start"),
])
def test_silver_quarantines_invalid_rows(spark, changes, issue):
    tables = silver(spark, [trip("a", **changes)])
    assert tables["fact_trip"].count() == 0
    assert issue in tables["quarantine_trip"].first().quality_issues


def test_gold_reconciles_and_separates_area_roles(spark):
    tables = silver(spark, [trip("a"), trip("b", trip_total=None), trip("c", start="2025-01-02T01:00:00.000")])
    marts = build_marts(tables, "f" * 32)
    daily = {row.trip_date.isoformat(): row for row in marts["mart_daily_summary"].collect()}
    assert daily["2025-01-01"].trip_count == 2 and daily["2025-01-01"].revenue_trip_count == 1
    assert daily["2025-01-01"].known_revenue_usd == Decimal("14.75") and daily["2025-01-01"].revenue_coverage == 0.5
    roles = {row.area_role for row in marts["mart_area_demand_daily"].collect()}
    assert roles == {"pickup", "dropoff"}
    assert validate_marts(marts, tables["fact_trip"])["trip_rows"] == 3
