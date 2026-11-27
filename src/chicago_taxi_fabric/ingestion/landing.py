"""Immutable OneLake Files run folders; only success manifests are consumable by bronze."""
import hashlib
import json
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from chicago_taxi_fabric.ingestion.taxi_api import pages


def month_windows(start, end):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    if start >= end:
        raise ValueError("start must precede exclusive end")
    while start < end:
        next_month = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
        stop = min(next_month, end)
        yield start.isoformat(), stop.isoformat()
        start = stop


def run_identity(value):
    """Fabric pipeline run IDs are GUIDs; normalise them to 32 lowercase hex characters."""
    if value in (None, ""):
        return uuid.uuid4().hex
    normalised = str(value).replace("-", "").lower()
    if not re.fullmatch(r"[0-9a-f]{32}", normalised):
        raise ValueError("run_id must be a GUID or 32 hexadecimal characters")
    return normalised


def _write(path, report):
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def ingest(root, start, end, page_size=5000, token="", fetch=None, max_pages=50000, run_id=None):
    windows = list(month_windows(start, end))
    if date.fromisoformat(start).year < 2024:
        raise ValueError("Taxi source covers 2024 onward")
    root = Path(root)
    if not root.is_absolute():
        raise ValueError("Landing root must be an absolute path such as /lakehouse/default/Files/landing")
    run_id = run_identity(run_id)
    folder = root / "taxi_trips" / ("run_id=" + run_id)
    folder.mkdir(parents=True, exist_ok=False)
    report = dict(run_id=run_id, source="taxi_trips", status="running", start=start,
                  end_exclusive=end, started_at_utc=datetime.now(timezone.utc).isoformat(),
                  extracted_rows=0, files=[], windows=[])
    audit = folder / "audit.json"
    _write(audit, report)
    try:
        for window_start, window_end in windows:
            count = 0
            for index, rows in enumerate(pages(window_start, window_end, page_size, token, fetch, max_pages)):
                body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
                relative = f"start={window_start}/part-{index:06d}.json"
                path = folder / relative
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(body)
                # Paths are relative to the run folder so manifests stay valid across mounts/workspaces.
                report["files"].append(dict(path=relative, rows=len(rows), bytes=len(body),
                    sha256=hashlib.sha256(body).hexdigest(), window_start=window_start,
                    window_end_exclusive=window_end))
                count += len(rows)
                report["extracted_rows"] += len(rows)
                if (index + 1) % 100 == 0:
                    _write(audit, report)
            report["windows"].append(dict(start=window_start, end_exclusive=window_end, rows=count))
            _write(audit, report)
        report.update(status="success", completed_at_utc=datetime.now(timezone.utc).isoformat())
        _write(audit, report)
        _write(folder / "manifest.json", report)
        return report
    except Exception as error:
        (folder / "manifest.json").unlink(missing_ok=True)
        report.update(status="failed", completed_at_utc=datetime.now(timezone.utc).isoformat(),
                      error_type=type(error).__name__)
        # Do not persist exception text: request/auth errors can include tokens or headers.
        _write(audit, report)
        raise
