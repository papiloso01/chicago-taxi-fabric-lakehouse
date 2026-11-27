import json
import pytest


def fake_api(rows):
    """Return a fetch() that serves rows filtered by window and trip_id cursor, like Socrata."""
    from urllib.parse import urlparse, parse_qs
    def fetch(url, token=""):
        query = parse_qs(urlparse(url).query)
        where, limit = query["$where"][0], int(query["$limit"][0])
        start = where.split("trip_start_timestamp >= '")[1][:19]
        end = where.split("trip_start_timestamp < '")[1][:19]
        cursor = where.split("trip_id > '")[1][:-1] if "trip_id > '" in where else None
        chosen = sorted((row for row in rows if start <= row["trip_start_timestamp"][:19] < end
                         and (cursor is None or row["trip_id"] > cursor)), key=lambda row: row["trip_id"])
        return json.loads(json.dumps(chosen[:limit]))
    return fetch


def trip(trip_id, start="2025-01-01T01:00:00.000", **changes):
    row = dict(trip_id=trip_id, taxi_id="taxi-" + trip_id, company="Yellow Cab", payment_type="Credit Card",
               trip_start_timestamp=start, trip_end_timestamp=start[:11] + "01:15:00.000", trip_seconds="900",
               trip_miles="2.5", fare="12.50", tips="2.25", tolls="0", extras="0", trip_total="14.75",
               pickup_community_area="8", dropoff_community_area="32")
    row.update(changes)
    return {key: value for key, value in row.items() if value is not None}


@pytest.fixture
def make_trip():
    return trip


@pytest.fixture
def api():
    return fake_api
