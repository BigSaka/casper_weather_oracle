"""
Fetches weather readings from a primary source and cross-checks against a
secondary source to produce a confidence score. The agent only posts
on-chain if confidence clears the configured minimum (see config.py).

Swap `fetch_primary` / `fetch_secondary` for whatever APIs you actually
have keys for — Open-Meteo (no key required) is used here as a working
default so the scaffold runs out of the box; NOAA is the natural upgrade
for US regions if you want a government-grade primary source.
"""
from dataclasses import dataclass
from typing import Optional

import requests

from .config import (
    Region,
    METRIC_RAINFALL,
    METRIC_WIND_SPEED,
    METRIC_TEMPERATURE,
)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class RawReading:
    metric: int
    value: float
    timestamp: int


def _fetch_open_meteo(region: Region) -> dict:
    """Primary source: Open-Meteo, no API key required, good for an MVP."""
    params = {
        "latitude": region.latitude,
        "longitude": region.longitude,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "timezone": "UTC",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_current_readings(region: Region) -> list[RawReading]:
    """Returns one RawReading per tracked metric from the primary source."""
    data = _fetch_open_meteo(region)
    current = data["current"]
    ts = int(
        __import__("datetime")
        .datetime.fromisoformat(current["time"])
        .timestamp()
    )

    return [
        RawReading(METRIC_RAINFALL, float(current.get("precipitation", 0.0)), ts),
        RawReading(METRIC_WIND_SPEED, float(current.get("wind_speed_10m", 0.0)), ts),
        RawReading(METRIC_TEMPERATURE, float(current.get("temperature_2m", 0.0)), ts),
    ]


def fetch_secondary_check(region: Region, metric: int) -> Optional[float]:
    """
    Cross-check source for confidence scoring. This MVP stub returns None
    (meaning "no second source available", which the scorer treats as
    moderate confidence). Wire up a second free API (e.g. wttr.in,
    Open-Weather) here for a real confidence signal.
    """
    return None
