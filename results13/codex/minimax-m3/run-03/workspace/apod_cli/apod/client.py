"""Tiny urllib-based client for NASA's APOD API."""
from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

API_BASE = "https://api.nasa.gov/planetary/apod"
DEMO_KEY = "DEMO_KEY"


class ApodError(RuntimeError):
    """Raised when the APOD endpoint cannot be reached or returns bad data."""


@dataclass(frozen=True)
class ApodData:
    date: date
    title: str
    explanation: str
    media_type: str  # "image" | "video" | other
    url: str
    hdurl: Optional[str] = None
    copyright: Optional[str] = None
    service_version: Optional[str] = None

    @property
    def is_image(self) -> bool:
        return self.media_type == "image"

    @property
    def is_video(self) -> bool:
        return self.media_type == "video"


def _api_key() -> str:
    return os.environ.get("NASA_API_KEY") or DEMO_KEY


def _parse(payload: dict) -> ApodData:
    try:
        return ApodData(
            date=datetime.strptime(payload["date"], "%Y-%m-%d").date(),
            title=payload["title"].strip(),
            explanation=payload["explanation"].strip(),
            media_type=payload.get("media_type", "other"),
            url=payload["url"],
            hdurl=payload.get("hdurl"),
            copyright=(payload.get("copyright") or "").strip() or None,
            service_version=payload.get("service_version"),
        )
    except KeyError as exc:
        raise ApodError(f"Unexpected APOD payload (missing {exc.args[0]!r})") from exc


def _http_get(params: dict, timeout: float = 15.0) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{API_BASE}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "apod-cli/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        raise ApodError(f"HTTP {exc.code} from APOD: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ApodError(f"Network error contacting APOD: {exc.reason}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ApodError("APOD returned non-JSON response") from exc


def fetch_apod(day: Optional[date] = None, *, random_pick: bool = False) -> ApodData:
    """Fetch APOD for ``day``. If ``random_pick`` is True, ask the API for a
    random entry (count=1) instead of a specific date."""
    params = {"api_key": _api_key()}
    if random_pick:
        params.update({"count": 1})
    else:
        params["date"] = (day or date.today()).isoformat()

    payload = _http_get(params)
    if isinstance(payload, list):
        if not payload:
            raise ApodError("APOD returned an empty random selection")
        payload = payload[0]
    return _parse(payload)


def fetch_range(start: date, end: date) -> list[ApodData]:
    if end < start:
        raise ApodError("end date must be on or after start date")
    params = {
        "api_key": _api_key(),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    payload = _http_get(params)
    if not isinstance(payload, list):
        raise ApodError("Expected a list response for date range")
    return [_parse(item) for item in payload]


def pick_random_local(pool_size: int = 30) -> date:
    """Pick a random date in the last ``pool_size`` days for offline use."""
    today = date.today()
    delta = random.randint(0, pool_size)
    return today - timedelta(days=delta)
