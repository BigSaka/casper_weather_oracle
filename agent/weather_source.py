"""
Fetches weather readings from two independent sources and cross-checks
them to produce a confidence score.

Primary source:   Open-Meteo (no API key required)
Secondary source: wttr.in (no API key required)

Both are free, require no registration, and return current conditions
for any lat/lon — making real confidence scoring possible out of the box.
"""
import datetime
import logging
from dataclasses import dataclass
from typing import Optional

import requests

from .config import (
    Region,
    METRIC_RAINFALL,
    METRIC_WIND_SPEED,
    METRIC_TEMPERATURE,
)

log = logging.getLogger("weather-oracle-agent.weather")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
WTTR_URL = "https://wttr.in/{lat},{lon}?format=j1"

REQUEST_TIMEOUT = 15


@dataclass
class RawReading:
    metric: int
    value: float
    timestamp: int


# ─── PRIMARY SOURCE: Open-Meteo ──────────────────────────────────────────────

def _fetch_open_meteo(region: Region) -> dict:
    params = {
        "latitude": region.latitude,
        "longitude": region.longitude,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "timezone": "UTC",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_current_readings(region: Region) -> list[RawReading]:
    """Returns one RawReading per tracked metric from the primary source."""
    data = _fetch_open_meteo(region)
    current = data["current"]
    ts = int(
        datetime.datetime.fromisoformat(current["time"]).timestamp()
    )

    readings = [
        RawReading(METRIC_RAINFALL,    float(current.get("precipitation", 0.0)), ts),
        RawReading(METRIC_WIND_SPEED,  float(current.get("wind_speed_10m", 0.0)), ts),
        RawReading(METRIC_TEMPERATURE, float(current.get("temperature_2m", 0.0)), ts),
    ]

    log.info(
        "Open-Meteo readings: rain=%.1fmm wind=%.1fkm/h temp=%.1f°C",
        readings[0].value, readings[1].value, readings[2].value
    )
    return readings


# ─── SECONDARY SOURCE: wttr.in ───────────────────────────────────────────────

def _fetch_wttr(region: Region) -> Optional[dict]:
    """
    wttr.in JSON API returns current conditions including temp, wind, precip.
    Returns None if the request fails so the agent can continue with
    reduced confidence rather than crashing.
    """
    url = WTTR_URL.format(lat=region.latitude, lon=region.longitude)
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.warning("wttr.in fetch failed: %s — will use single-source confidence", e)
        return None


def fetch_secondary_check(region: Region, metric: int) -> Optional[float]:
    """
    Returns the secondary source value for a given metric, or None if
    the secondary source is unavailable.

    wttr.in units:
      - temp_C: degrees Celsius
      - windspeedKmph: km/h
      - precipMM: mm (hourly precipitation)
    """
    data = _fetch_wttr(region)
    if data is None:
        return None

    try:
        current = data["current_condition"][0]
        if metric == METRIC_TEMPERATURE:
            return float(current["temp_C"])
        elif metric == METRIC_WIND_SPEED:
            return float(current["windspeedKmph"])
        elif metric == METRIC_RAINFALL:
            return float(current.get("precipMM", 0.0))
        return None
    except (KeyError, IndexError, ValueError) as e:
        log.warning("failed to parse wttr.in response for metric %d: %s", metric, e)
        return None
