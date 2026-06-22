"""
Shared config for the weather oracle agent.

All thresholds and fixed-point scaling live here so the agent and any
reconciliation scripts agree on units without re-deriving them.
"""
import os
from dataclasses import dataclass


# Fixed-point scale used on-chain: value_fp = round(value * FP_SCALE)
FP_SCALE = 100

# Metric discriminants, must match Metric enum in weather_oracle.rs
METRIC_RAINFALL = 0
METRIC_WIND_SPEED = 1
METRIC_TEMPERATURE = 2

METRIC_NAMES = {
    METRIC_RAINFALL: "rainfall_mm",
    METRIC_WIND_SPEED: "wind_speed_kmh",
    METRIC_TEMPERATURE: "temperature_c",
}


@dataclass
class Region:
    name: str
    latitude: float
    longitude: float


# MVP tracks a single region. Swap this for your chosen location.
DEFAULT_REGION = Region(name="Miami, FL", latitude=25.7617, longitude=-80.1918)


@dataclass
class AgentConfig:
    region: Region
    poll_interval_seconds: int = 3600  # hourly
    primary_weather_api_key: str = os.environ.get("WEATHER_API_KEY", "")
    secondary_weather_api_key: str = os.environ.get("WEATHER_API_KEY_BACKUP", "")
    casper_node_url: str = os.environ.get(
        "CASPER_NODE_URL", "https://node.testnet.casper.network/rpc"
    )
    chain_name: str = os.environ.get("CASPER_CHAIN_NAME", "casper-test")
    contract_hash: str = os.environ.get("ORACLE_CONTRACT_HASH", "")
    agent_secret_key_path: str = os.environ.get(
        "AGENT_SECRET_KEY_PATH", "./keys/agent_secret_key.pem"
    )
    # Confidence below this drops the reading from being posted at all —
    # better to skip a tick than post a number you don't trust.
    min_confidence_bps_to_post: int = 6000  # 60%


def to_fixed_point(value: float) -> int:
    """Convert a float reading to the on-chain fixed-point integer."""
    return round(value * FP_SCALE)


def from_fixed_point(value_fp: int) -> float:
    return value_fp / FP_SCALE
