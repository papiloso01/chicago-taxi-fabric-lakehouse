import json
import pytest
from chicago_taxi_fabric.ingestion.landing import ingest, month_windows, run_identity
from chicago_taxi_fabric.transformations.bronze.landing_manifest import stage_run

GUID = "0F8FAD5B-D9CB-469F-A165-70867728950E"


def test_month_windows_split_end_exclusive():
    assert list(month_windows("2025-01-15", "2025-03-02")) == [
        ("2025-01-15", "2025-02-01"), ("2025-02-01", "2025-03-01"), ("2025-03-01", "2025-03-02")]


def test_fabric_guid_run_id_normalised():
    assert run_identity(GUID) == "0f8fad5bd9cb469fa16570867728950e"
    with pytest.raises(ValueError):
        run_identity("../escape")


def test_success_manifest_and_stage(tmp_path, api, make_trip):
    rows = [make_trip("a"), make_trip("b"), make_trip("c", start="2025-02-01T09:00:00.000")]
    report = ingest(tmp_path, "2025-01-01", "2025-03-01", page_size=2, fetch=api(rows), run_id=GUID)
    run = tmp_path / "taxi_trips" / ("run_id=" + report["run_id"])
    assert report["status"] == "success" and report["extracted_rows"] == 3
    assert [w["rows"] for w in report["windows"]] == [2, 1]
    assert all(not item["path"].startswith("/") for item in report["files"])
    manifest, stage = stage_run(run, tmp_path / "stage")
    staged = [json.loads(line) for line in (stage / "part-000000.json").read_text().splitlines()]
    assert [row["trip_id"] for row in staged] == ["a", "b", "c"]
    assert json.loads(staged[0]["raw_payload"]) == rows[0]


def test_rerun_with_same_id_never_overwrites(tmp_path, api, make_trip):
    ingest(tmp_path, "2025-01-01", "2025-01-02", fetch=api([make_trip("a")]), run_id=GUID)
    with pytest.raises(FileExistsError):
        ingest(tmp_path, "2025-01-01", "2025-01-02", fetch=api([make_trip("a")]), run_id=GUID)


def test_failed_run_has_audit_but_no_manifest(tmp_path):
    def broken(url, token):
        raise ConnectionError("token=secret")
    with pytest.raises(ConnectionError):
        ingest(tmp_path, "2025-01-01", "2025-01-02", fetch=broken, run_id=GUID)
    run = tmp_path / "taxi_trips" / ("run_id=" + run_identity(GUID))
    audit = (run / "audit.json").read_text()
    assert not (run / "manifest.json").exists()
    assert '"failed"' in audit and "secret" not in audit
    with pytest.raises(ValueError, match="no success manifest"):
        stage_run(run)


def test_tampered_landing_file_rejected(tmp_path, api, make_trip):
    report = ingest(tmp_path, "2025-01-01", "2025-01-02", fetch=api([make_trip("a")]), run_id=GUID)
    run = tmp_path / "taxi_trips" / ("run_id=" + report["run_id"])
    (run / report["files"][0]["path"]).write_text("[]")
    with pytest.raises(ValueError, match="does not match"):
        stage_run(run, tmp_path / "stage")


def test_relative_landing_root_rejected(api):
    with pytest.raises(ValueError, match="absolute"):
        ingest("Files/landing", "2025-01-01", "2025-01-02", fetch=api([]))
