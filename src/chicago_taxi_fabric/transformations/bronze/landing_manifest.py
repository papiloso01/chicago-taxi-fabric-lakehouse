"""Verify a landing run against its success manifest and stage one JSON line per trip."""
import hashlib
import json
import re
import uuid
from pathlib import Path


def read_manifest(run_path):
    run_path = Path(run_path)
    if not re.fullmatch(r"run_id=[0-9a-f]{32}", run_path.name):
        raise ValueError("Expected a run_id=<32 hex> landing folder")
    manifest_path = run_path / "manifest.json"
    if not manifest_path.exists():
        raise ValueError("Landing run has no success manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "success" or "run_id=" + str(manifest.get("run_id")) != run_path.name:
        raise ValueError("Manifest is not a successful manifest for this run")
    if sum(item["rows"] for item in manifest["files"]) != manifest["extracted_rows"]:
        raise ValueError("Manifest file rows do not sum to extracted rows")
    return manifest


def stage_run(run_path, stage_root=None):
    """Return (manifest, stage folder). Files are hash-checked; payloads are kept verbatim."""
    run_path = Path(run_path)
    manifest = read_manifest(run_path)
    stage = Path(stage_root or run_path / "_bronze_stage") / uuid.uuid4().hex
    stage.mkdir(parents=True)
    with open(stage / "part-000000.json", "w", encoding="utf-8") as out:
        for item in manifest["files"]:
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Manifest file paths must stay inside the run folder")
            body = (run_path / relative).read_bytes()
            if len(body) != item["bytes"] or hashlib.sha256(body).hexdigest() != item["sha256"]:
                raise ValueError("Landing file does not match manifest: " + item["path"])
            rows = json.loads(body)
            if not isinstance(rows, list) or len(rows) != item["rows"]:
                raise ValueError("Landing file row count does not match manifest")
            for row in rows:
                payload = json.dumps(row, ensure_ascii=False, sort_keys=True)
                out.write(json.dumps(dict(trip_id=row.get("trip_id"), raw_payload=payload,
                    payload_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                    landing_run_id=manifest["run_id"], source_file=item["path"],
                    extracted_at_utc=manifest["completed_at_utc"]), ensure_ascii=False) + "\n")
    return manifest, stage
