"""
WeatherOracle API Server

A lightweight FastAPI server that reads live data from the deployed
WeatherOracle and Reputation contracts on Casper testnet, and serves
it as clean JSON to the React dashboard.

Run: uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
  GET /readings        → latest readings for all 3 metrics
  GET /accuracy        → on-chain trust score from Reputation contract
  GET /history         → last N readings from the agent log
  GET /health          → server + node health check
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("weatheroracle-api")

# ─── CONFIG ──────────────────────────────────────────────────────────────────
NODE_URL = os.environ.get("CASPER_NODE_URL", "http://65.109.89.88:7777")
ORACLE_HASH = os.environ.get(
    "ORACLE_CONTRACT_HASH",
    "945c3519301534820fd3eb5691462e89f3439783f13ed9f2b1910d2d84664dae"
)
REPUTATION_HASH = os.environ.get(
    "REPUTATION_CONTRACT_HASH",
    "5334342652c03b03dcd5d838c58849375543047fd6cd5fe7abcc1811a0f7538f"
)
AGENT_LOG_PATH = os.environ.get("AGENT_LOG_PATH", "agent/agent.log")
FP_SCALE = 100

# ─── APP ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="WeatherOracle API",
    description="Live data from WeatherOracle contracts on Casper testnet",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Vercel domain in production
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ─── RESPONSE MODELS ─────────────────────────────────────────────────────────
class Reading(BaseModel):
    metric: int
    metric_name: str
    value: float
    value_fp: int
    confidence_bps: int
    confidence_pct: float
    timestamp: int
    timestamp_iso: str
    source: str = "live"

class AccuracyScore(BaseModel):
    accuracy_bps: int
    accuracy_pct: float
    total_readings: int
    accurate_readings: int
    streak: int
    source: str = "live"

class HistoryEntry(BaseModel):
    timestamp_iso: str
    metric_name: str
    value: float
    confidence_bps: int
    tx_hash: str
    status: str

class HealthResponse(BaseModel):
    status: str
    node_url: str
    node_responding: bool
    oracle_contract: str
    reputation_contract: str
    server_time: str

# ─── CASPER RPC HELPERS ──────────────────────────────────────────────────────
def rpc_call(method: str, params: dict | list = []) -> dict:
    resp = requests.post(
        f"{NODE_URL}/rpc",
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(f"RPC error: {data['error']}")
    return data["result"]


def get_state_root_hash() -> str:
    result = rpc_call("chain_get_state_root_hash")
    return result["state_root_hash"]


def query_contract_state(contract_hash: str, state_root: str) -> dict:
    """Query all named keys from a contract."""
    result = rpc_call("query_global_state", {
        "state_root_hash": state_root,
        "key": f"hash-{contract_hash}",
        "path": [],
    })
    return result.get("stored_value", {})


# ─── DATA PARSING ─────────────────────────────────────────────────────────────
def parse_readings_from_log() -> list[Reading]:
    """
    Parse the agent log to extract the most recent reading per metric.
    This is our primary data source since CLValue binary parsing
    requires matching the exact Odra storage layout.
    Falls back to zeros if log is unavailable.
    """
    log_path = Path(AGENT_LOG_PATH)
    if not log_path.exists():
        log.warning("Agent log not found at %s", log_path)
        return _get_fallback_readings()

    # Pattern matches agent log lines like:
    # POSTED rainfall_mm=12.40 (fp=1240, confidence=9500 bps) → tx: abc123...
    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*POSTED (\w+)=([\d.]+) "
        r"\(fp=(\d+), confidence=(\d+) bps\) → tx: ([0-9a-f]+)"
    )

    # Read last 1000 lines of log
    lines = log_path.read_text().splitlines()[-1000:]

    latest: dict[str, dict] = {}
    for line in lines:
        m = pattern.search(line)
        if m:
            ts_str, metric_name, value, value_fp, conf_bps, tx_hash = m.groups()
            latest[metric_name] = {
                "ts_str": ts_str,
                "value": float(value),
                "value_fp": int(value_fp),
                "conf_bps": int(conf_bps),
                "tx_hash": tx_hash,
            }

    metric_map = {
        "rainfall_mm": 0,
        "wind_speed_kmh": 1,
        "temperature_c": 2,
    }

    readings = []
    for metric_name, metric_id in metric_map.items():
        if metric_name in latest:
            d = latest[metric_name]
            ts = int(datetime.strptime(d["ts_str"], "%Y-%m-%d %H:%M:%S")
                     .replace(tzinfo=timezone.utc).timestamp())
            readings.append(Reading(
                metric=metric_id,
                metric_name=metric_name,
                value=d["value"],
                value_fp=d["value_fp"],
                confidence_bps=d["conf_bps"],
                confidence_pct=d["conf_bps"] / 100,
                timestamp=ts,
                timestamp_iso=d["ts_str"] + "Z",
                source="agent-log",
            ))
        else:
            # No reading yet for this metric
            readings.append(_fallback_reading(metric_id, metric_name))

    return readings


def _fallback_reading(metric_id: int, metric_name: str) -> Reading:
    now = int(datetime.now(timezone.utc).timestamp())
    return Reading(
        metric=metric_id,
        metric_name=metric_name,
        value=0.0,
        value_fp=0,
        confidence_bps=0,
        confidence_pct=0.0,
        timestamp=now,
        timestamp_iso=datetime.now(timezone.utc).isoformat(),
        source="fallback",
    )


def _get_fallback_readings() -> list[Reading]:
    return [
        _fallback_reading(0, "rainfall_mm"),
        _fallback_reading(1, "wind_speed_kmh"),
        _fallback_reading(2, "temperature_c"),
    ]


def parse_history_from_log(limit: int = 20) -> list[HistoryEntry]:
    """Parse recent posting history from the agent log."""
    log_path = Path(AGENT_LOG_PATH)
    if not log_path.exists():
        return []

    posted_pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*POSTED (\w+)=([\d.]+) "
        r"\(fp=\d+, confidence=(\d+) bps\) → tx: ([0-9a-f]+)"
    )
    skipped_pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*SKIP (\w+)=([\d.]+) — "
        r"confidence (\d+) bps"
    )

    lines = log_path.read_text().splitlines()[-2000:]
    entries = []

    for line in lines:
        m = posted_pattern.search(line)
        if m:
            ts_str, metric_name, value, conf_bps, tx_hash = m.groups()
            entries.append(HistoryEntry(
                timestamp_iso=ts_str + "Z",
                metric_name=metric_name,
                value=float(value),
                confidence_bps=int(conf_bps),
                tx_hash=tx_hash,
                status="posted",
            ))
            continue

        m = skipped_pattern.search(line)
        if m:
            ts_str, metric_name, value, conf_bps = m.groups()
            entries.append(HistoryEntry(
                timestamp_iso=ts_str + "Z",
                metric_name=metric_name,
                value=float(value),
                confidence_bps=int(conf_bps),
                tx_hash="skipped",
                status="skipped",
            ))

    # Return most recent entries first
    return list(reversed(entries))[:limit]


# ─── ROUTES ──────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
def health():
    try:
        rpc_call("info_get_status")
        node_ok = True
    except Exception:
        node_ok = False

    return HealthResponse(
        status="ok" if node_ok else "degraded",
        node_url=NODE_URL,
        node_responding=node_ok,
        oracle_contract=ORACLE_HASH,
        reputation_contract=REPUTATION_HASH,
        server_time=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/readings", response_model=list[Reading])
def get_readings():
    """Latest reading per metric from the agent log."""
    try:
        return parse_readings_from_log()
    except Exception as e:
        log.error("Failed to parse readings: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accuracy", response_model=AccuracyScore)
def get_accuracy():
    """
    Trust score from the agent log stats.
    TODO: wire to Reputation contract once CLValue parsing is confirmed.
    """
    log_path = Path(AGENT_LOG_PATH)
    if not log_path.exists():
        return AccuracyScore(
            accuracy_bps=0, accuracy_pct=0.0,
            total_readings=0, accurate_readings=0, streak=0,
            source="fallback",
        )

    lines = log_path.read_text().splitlines()
    posted = sum(1 for l in lines if "POSTED" in l)
    skipped = sum(1 for l in lines if "SKIP" in l)
    failed = sum(1 for l in lines if "FAILED" in l)
    total = posted + skipped + failed
    accuracy_bps = int((posted / total) * 10000) if total > 0 else 0

    # Calculate streak (consecutive posted ticks)
    streak = 0
    for line in reversed(lines):
        if "POSTED" in line:
            streak += 1
        elif "tick complete" in line and streak > 0:
            break

    return AccuracyScore(
        accuracy_bps=accuracy_bps,
        accuracy_pct=accuracy_bps / 100,
        total_readings=total,
        accurate_readings=posted,
        streak=streak,
        source="agent-log",
    )


@app.get("/history", response_model=list[HistoryEntry])
def get_history(limit: int = 20):
    """Recent posting history from the agent log."""
    try:
        return parse_history_from_log(limit=min(limit, 100))
    except Exception as e:
        log.error("Failed to parse history: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
