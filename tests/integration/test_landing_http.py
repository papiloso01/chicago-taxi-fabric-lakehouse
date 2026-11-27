"""Real HTTP extraction into landing against a loopback fixture API; no cloud credentials."""
import json
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from chicago_taxi_fabric.ingestion import taxi_api
from chicago_taxi_fabric.ingestion.landing import ingest
from tests.conftest import fake_api, trip

ROWS = [trip(f"t{i:02d}") for i in range(5)]


class Handler(BaseHTTPRequestHandler):
    calls = []

    def do_GET(self):
        Handler.calls.append(self.headers.get("X-App-Token"))
        if len(Handler.calls) == 1:
            self.send_response(503)
            self.end_headers()
            return
        body = json.dumps(fake_api(ROWS)("http://x" + self.path)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    Handler.calls = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}/resource/ajtu-isnz.json"
    httpd.shutdown()


def test_http_extraction_retries_and_lands_all_rows(tmp_path, server, monkeypatch):
    monkeypatch.setattr(taxi_api, "ENDPOINT", server)
    monkeypatch.setattr(taxi_api.time, "sleep", lambda seconds: None)
    original = taxi_api.pages
    monkeypatch.setattr("chicago_taxi_fabric.ingestion.landing.pages",
                        partial(lambda *a, **k: original(*a, endpoint=server, **k)))
    report = ingest(tmp_path, "2025-01-01", "2025-01-02", page_size=2, token="app-token")
    assert report["status"] == "success" and report["extracted_rows"] == 5
    assert len(report["files"]) == 3
    assert Handler.calls[0] == "app-token"
