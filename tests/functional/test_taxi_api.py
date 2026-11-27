from urllib.error import HTTPError
import pytest
from chicago_taxi_fabric.ingestion import taxi_api
from chicago_taxi_fabric.ingestion.taxi_api import pages


def test_keyset_pagination_exhausts_window(api, make_trip):
    rows = [make_trip(f"t{i:03d}") for i in range(7)] + [make_trip("late", start="2025-01-02T00:00:00.000")]
    result = list(pages("2025-01-01", "2025-01-02", page_size=3, fetch=api(rows)))
    assert [len(page) for page in result] == [3, 3, 1]
    assert [row["trip_id"] for page in result for row in page] == [f"t{i:03d}" for i in range(7)]


def test_non_advancing_keys_rejected():
    with pytest.raises(ValueError, match="non-advancing"):
        list(pages("2025-01-01", "2025-01-02", page_size=5, fetch=lambda url, token: [{"trip_id": "b"}, {"trip_id": "a"}]))


def test_page_limit_is_an_incomplete_run(api, make_trip):
    with pytest.raises(RuntimeError, match="incomplete"):
        list(pages("2025-01-01", "2025-01-02", page_size=1, max_pages=2, fetch=api([make_trip(str(i)) for i in range(5)])))


@pytest.mark.parametrize("start,end", [("2025-01-02", "2025-01-01"), ("2023-12-31", "2024-01-02")])
def test_invalid_windows_rejected(start, end):
    with pytest.raises(ValueError):
        list(pages(start, end, fetch=lambda url, token: []))


def test_transient_errors_retry_then_succeed(monkeypatch):
    calls = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, *args): return b"[]"
    def fake_urlopen(request, timeout):
        calls.append(request)
        if len(calls) < 3:
            raise HTTPError(request.full_url, 503, "busy", {}, None)
        return Response()
    monkeypatch.setattr(taxi_api, "urlopen", fake_urlopen)
    assert taxi_api.request_rows("https://example.test/x", sleep=lambda seconds: None) == []
    assert len(calls) == 3


def test_client_errors_are_not_retried(monkeypatch):
    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 400, "bad", {}, None)
    monkeypatch.setattr(taxi_api, "urlopen", fake_urlopen)
    with pytest.raises(HTTPError):
        taxi_api.request_rows("https://example.test/x", sleep=lambda seconds: None)
