"""Chicago-local inclusive-start/exclusive-end loading windows."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")


def daily_window(now=None):
    now = now or datetime.now(CHICAGO)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    end = now.astimezone(CHICAGO).date()
    return (end - timedelta(days=1)).isoformat(), end.isoformat()


def year_window(year, today=None):
    today = today or datetime.now(CHICAGO).date()
    if not 1 <= year < today.year:
        raise ValueError("Choose a completed calendar year")
    return date(year, 1, 1).isoformat(), date(year + 1, 1, 1).isoformat()


def resolve_window(mode, start="", end="", year="", now=None):
    """Turn pipeline parameters into one explicit window; Fabric passes every parameter as text."""
    if mode == "daily":
        return daily_window(now)
    if mode == "year":
        if not str(year).isdigit():
            raise ValueError("year mode needs a numeric year")
        return year_window(int(year), (now or datetime.now(CHICAGO)).astimezone(CHICAGO).date())
    if mode == "range":
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first >= last:
            raise ValueError("start must precede exclusive end")
        return first.isoformat(), last.isoformat()
    raise ValueError("mode must be daily, year or range")
