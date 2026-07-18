"""
WeatherOracle API Server - reads from GitHub Gist for live data.
"""
import json
import logging
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("weatheroracle-api")

NODE_URL = os.environ.get("CASPER_NODE_URL", "http://65.109.89.88:7777")
ORACLE_HASH = os.environ.get("ORACLE_CONTRACT_HASH", "945c3519301534820fd3eb5691462e89f3439783f13ed9f2b1910d2d84664dae")
REPUTATION_HASH = os.environ.get("REPUTATION_CONTRACT_HASH", "5334342652c03b03dcd5d838c58849375543047fd6cd5fe7abcc1811a0f7538f")
GIST_ID = os.environ.get("GIST_ID", "0955aac10d21ab78b31d11b8e2f1db27")
GIST_FILENAME = "readings.json"

app = FastAPI(title="WeatherOracle API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


class Reading(BaseModel):
    metric: int
    metric_name: str
    value: float
    confidence_bps: int
    confidence_pct: float
    timestamp: int
    timestamp_iso: str
    tx_hash: str
    source: str = "gist"


class AccuracyScore(BaseModel):
    accuracy_pct: float
    total_readings: int
    streak: int
    last_updated: str
    source: str = "gist"


class HealthResponse(BaseModel):
    status: str
    node_responding: bool
    gist_responding: bool
    server_time: str


def fetch_gist() -> dict:
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        resp = requests.get(url, timeout=10,
                           headers={"Accept": "application/vnd.github.v3+json"})
        resp.raise_for_status()
        content = resp.json()["files"][GIST_FILENAME]["content"]
        return json.loads(content)
    except Exception as e:
        log.error("Failed to fetch gist: %s", e)
        return {}


@app.get("/health", response_model=HealthResponse)
def health():
    node_ok = False
    gist_ok = False
    try:
        requests.post(f"{NODE_URL}/rpc",
                     json={"jsonrpc":"2.0","id":1,"method":"info_get_status","params":[]},
                     timeout=8)
        node_ok = True
    except Exception:
        pass
    try:
        fetch_gist()
        gist_ok = True
    except Exception:
        pass
    return HealthResponse(
        status="ok" if gist_ok else "degraded",
        node_responding=node_ok,
        gist_responding=gist_ok,
        server_time=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/readings", response_model=list[Reading])
def get_readings():
    data = fetch_gist()
    if not data:
        raise HTTPException(status_code=503, detail="Gist unavailable")

    metric_map = [
        (0, "rainfall",   "rainfall_mm"),
        (1, "wind_speed", "wind_speed_kmh"),
        (2, "temperature","temperature_c"),
    ]

    results = []
    for metric_id, gist_key, metric_name in metric_map:
        d = data.get(gist_key, {})
        results.append(Reading(
            metric=metric_id,
            metric_name=metric_name,
            value=d.get("value", 0.0),
            confidence_bps=d.get("confidence_bps", 0),
            confidence_pct=d.get("confidence_pct", 0.0),
            timestamp=d.get("timestamp", 0),
            timestamp_iso=d.get("timestamp_iso", ""),
            tx_hash=d.get("tx_hash", ""),
            source="gist",
        ))
    return results


@app.get("/accuracy", response_model=AccuracyScore)
def get_accuracy():
    data = fetch_gist()
    if not data:
        return AccuracyScore(
            accuracy_pct=0.0, total_readings=0,
            streak=0, last_updated="", source="fallback"
        )
    total = data.get("total_readings", 0)
    return AccuracyScore(
        accuracy_pct=round((total / max(total, 1)) * 100, 1),
        total_readings=total,
        streak=data.get("streak", 0),
        last_updated=data.get("last_updated", ""),
        source="gist",
    )


@app.get("/history")
def get_history():
    data = fetch_gist()
    if not data:
        return []
    history = data.get("history", [])
    return history[-20:]
