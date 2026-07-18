"""
gist_sync.py
Syncs WeatherOracle readings to/from a GitHub Gist so the Railway
API server can read live data posted by the local agent.
"""
import json
import logging
import os
from datetime import datetime, timezone

import requests

log = logging.getLogger("weatheroracle-agent.gist")

GIST_ID = os.environ.get("GIST_ID", "0955aac10d21ab78b31d11b8e2f1db27")
GIST_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GIST_FILENAME = "readings.json"
GIST_API = f"https://api.github.com/gists/{GIST_ID}"


def _headers():
    return {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def read_gist() -> dict:
    """Read current readings from the Gist."""
    try:
        resp = requests.get(GIST_API, headers=_headers(), timeout=10)
        resp.raise_for_status()
        content = resp.json()["files"][GIST_FILENAME]["content"]
        return json.loads(content)
    except Exception as e:
        log.warning("Failed to read gist: %s", e)
        return {}


def update_gist(data: dict) -> bool:
    """Write updated readings to the Gist."""
    try:
        payload = {
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(data, indent=2)
                }
            }
        }
        resp = requests.patch(GIST_API, headers=_headers(),
                              json=payload, timeout=10)
        resp.raise_for_status()
        log.info("Gist updated successfully")
        return True
    except Exception as e:
        log.error("Failed to update gist: %s", e)
        return False


def post_reading(metric_name: str, value: float, confidence_bps: int,
                 tx_hash: str, timestamp: int) -> bool:
    """
    Update a single metric's reading in the Gist.
    Call this after each successful on-chain submission.
    """
    if not GIST_TOKEN:
        log.warning("GITHUB_TOKEN not set — skipping Gist sync")
        return False

    # Read current state
    data = read_gist() or {
        "rainfall":    {"value": 0.0, "confidence": 0, "timestamp": 0, "tx_hash": ""},
        "wind_speed":  {"value": 0.0, "confidence": 0, "timestamp": 0, "tx_hash": ""},
        "temperature": {"value": 0.0, "confidence": 0, "timestamp": 0, "tx_hash": ""},
        "total_readings": 0,
        "streak": 0,
        "last_updated": "",
    }

    # Map agent metric names to gist keys
    key_map = {
        "rainfall_mm":    "rainfall",
        "wind_speed_kmh": "wind_speed",
        "temperature_c":  "temperature",
    }
    gist_key = key_map.get(metric_name, metric_name)

    # Update the metric
    data[gist_key] = {
        "value":          value,
        "confidence_bps": confidence_bps,
        "confidence_pct": confidence_bps / 100,
        "timestamp":      timestamp,
        "tx_hash":        tx_hash,
        "timestamp_iso":  datetime.fromtimestamp(
                              timestamp, tz=timezone.utc
                          ).isoformat(),
    }

    # Update metadata
    data["total_readings"] = data.get("total_readings", 0) + 1
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    return update_gist(data)
