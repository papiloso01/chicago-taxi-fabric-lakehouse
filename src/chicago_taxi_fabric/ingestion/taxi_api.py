"""Bounded Socrata extraction with trip-ID keyset pagination and transient retries."""
import json
import time
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://data.cityofchicago.org/resource/ajtu-isnz.json"
RETRYABLE = (429, 500, 502, 503, 504)


def request_rows(url, token="", sleep=time.sleep):
    headers = {"User-Agent": "chicago-taxi-fabric-lakehouse/0.1"}
    if token:
        headers["X-App-Token"] = token
    for attempt in range(5):
        try:
            with urlopen(Request(url, headers=headers), timeout=90) as response:
                value = json.load(response)
            if not isinstance(value, list):
                raise ValueError("Expected a JSON array from taxi API")
            return value
        except (HTTPError, URLError, TimeoutError) as error:
            if isinstance(error, HTTPError) and error.code not in RETRYABLE:
                raise
            if attempt == 4:
                raise
            sleep(2 ** attempt)


def pages(start, end, page_size=5000, token="", fetch=None, max_pages=50000, endpoint=ENDPOINT):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    if start >= end or start.year < 2024:
        raise ValueError("Use a nonempty end-exclusive window within the 2024+ source")
    if not 1 <= page_size <= 50000 or max_pages < 1:
        raise ValueError("Invalid page limits")
    fetch = fetch or request_rows
    cursor = None
    for _ in range(max_pages):
        where = f"trip_start_timestamp >= '{start}T00:00:00' AND trip_start_timestamp < '{end}T00:00:00'"
        if cursor is not None:
            where += " AND trip_id > '" + cursor.replace("'", "''") + "'"
        query = urlencode({"$where": where, "$order": "trip_id ASC", "$limit": page_size})
        rows = fetch(endpoint + "?" + query, token)
        if not isinstance(rows, list) or len(rows) > page_size:
            raise ValueError("Invalid API page")
        if not rows:
            return
        previous = cursor
        for row in rows:
            key = row.get("trip_id") if isinstance(row, dict) else None
            if not isinstance(key, str) or not key or (previous is not None and key <= previous):
                raise ValueError("Missing, duplicate or non-advancing trip ID")
            previous = key
        yield rows
        cursor = previous
        if len(rows) < page_size:
            return
    raise RuntimeError("Page limit reached before source exhaustion; run is incomplete")
