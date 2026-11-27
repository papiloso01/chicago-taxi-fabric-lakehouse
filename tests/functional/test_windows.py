from datetime import date, datetime, timezone
import pytest
from chicago_taxi_fabric.ingestion.windows import daily_window, year_window, resolve_window

NOW = datetime(2026, 1, 2, 2, tzinfo=timezone.utc)


def test_daily_uses_chicago_date_not_utc_date():
    assert daily_window(NOW) == ("2025-12-31", "2026-01-01")


def test_naive_clock_rejected():
    with pytest.raises(ValueError, match="timezone"):
        daily_window(datetime(2026, 1, 1))


def test_completed_year_end_is_exclusive():
    assert year_window(2025, date(2026, 10, 14)) == ("2025-01-01", "2026-01-01")


@pytest.mark.parametrize("year", [0, 2026, 2027])
def test_incomplete_year_rejected(year):
    with pytest.raises(ValueError):
        year_window(year, date(2026, 10, 14))


def test_pipeline_text_parameters_resolve():
    assert resolve_window("daily", now=NOW) == ("2025-12-31", "2026-01-01")
    assert resolve_window("year", year="2024", now=datetime(2026, 6, 1, tzinfo=timezone.utc)) == ("2024-01-01", "2025-01-01")
    assert resolve_window("range", "2025-01-01", "2025-02-01") == ("2025-01-01", "2025-02-01")


@pytest.mark.parametrize("args", [("range", "2025-02-01", "2025-01-01"), ("year", "", "", "abc"), ("weekly",)])
def test_bad_pipeline_parameters_rejected(args):
    with pytest.raises(ValueError):
        resolve_window(*args, now=NOW)
