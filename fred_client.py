"""Minimal FRED client with no UI dependencies (requests only).

The API key is read from the FRED_API_KEY environment variable. Errors raised
from this module never include the request URL, because the URL contains the
API key as a query parameter.
"""

import datetime
import os

import requests

FRED_DATA_URL = "https://api.stlouisfed.org/fred/series/observations"
DEFAULT_TIMEOUT = 30  # seconds


class FredError(RuntimeError):
    """Raised when FRED data cannot be retrieved."""


def get_api_key():
    """Return the FRED API key from the environment, or None if unset/blank."""
    key = os.environ.get("FRED_API_KEY", "").strip()
    return key or None


def get_series_latest(series_id, api_key=None, timeout=DEFAULT_TIMEOUT):
    """Return (date, value) for the latest non-missing observation of a series.

    `date` is a datetime.date and `value` is a float. FRED marks missing
    observations (e.g. market holidays for daily yields) with ".", so those
    are skipped.

    Raises FredError if no API key is configured, the request fails, or the
    series has no non-missing observations in the most recent window.
    """
    key = api_key or get_api_key()
    if not key:
        raise FredError("FRED_API_KEY environment variable is not set.")

    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 100,
    }
    try:
        resp = requests.get(FRED_DATA_URL, params=params, timeout=timeout)
    except requests.RequestException as exc:
        # Don't chain/format the original exception: its message includes the URL (and key).
        raise FredError(f"Request for {series_id} failed: {type(exc).__name__}") from None

    if resp.status_code != 200:
        raise FredError(f"FRED returned HTTP {resp.status_code} for {series_id}")

    try:
        observations = resp.json().get("observations", [])
    except ValueError:
        raise FredError(f"FRED returned invalid JSON for {series_id}") from None

    for obs in observations:
        raw = obs.get("value", ".")
        if raw in (".", "", None):
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        date = datetime.date.fromisoformat(obs["date"])
        return date, value

    raise FredError(f"No non-missing observations found for {series_id}")


if __name__ == "__main__":
    import sys

    for sid in sys.argv[1:] or ["DGS10"]:
        d, v = get_series_latest(sid)
        print(f"{sid}\t{d.isoformat()}\t{v}")
