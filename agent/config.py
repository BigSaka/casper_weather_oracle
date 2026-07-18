"""
Shared config for the weather oracle agent.

All thresholds and fixed-point scaling live here so the agent and any
reconciliation scripts agree on units without re-deriving them.
"""
import os
from dataclasses import dataclass, field


# Fixed-point scale used on-chain: value_fp = round(value * FP_SCALE)
FP_SCALE = 100

# Metric discriminants — must match Metric enum in weather_oracle.rs
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


# Default region — change to your target location
DEFAULT_REGION = Region(name="Miami, FL", latitude=25.7617, longitude=-80.1918)


@dataclass
class AgentConfig:
    region: Region

    # How often to post readings (seconds)
    # 300 = every 5 minutes | 600 = every 10 minutes | 3600 = hourly
    poll_interval_seconds: int = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

    # Casper node and chain config
    casper_node_url: str = os.environ.get(
        "CASPER_NODE_URL", "http://65.109.89.88:7777"
    )
    chain_name: str = os.environ.get("CASPER_CHAIN_NAME", "casper-test")

    # Contract hashes
    contract_hash: str = os.environ.get(
        "ORACLE_CONTRACT_HASH",
        "945c3519301534820fd3eb5691462e89f3439783f13ed9f2b1910d2d84664dae"
    )
    reputation_hash: str = os.environ.get(
        "REPUTATION_CONTRACT_HASH",
        "5334342652c03b03dcd5d838c58849375543047fd6cd5fe7abcc1811a0f7538f"
    )

    # Path to the contracts/weather_oracle_new directory (where cargo lives)
    # This is used by chain_client.py to shell out to the Odra CLI
    cli_project_dir: str = os.environ.get(
        "CLI_PROJECT_DIR",
        "/mnt/c/Users/Issachar/Downloads/casper-weather-oracle/contracts/weather_oracle_new"
    )

    # Gas per contract call
    gas_per_call: str = os.environ.get("GAS_PER_CALL", "3cspr")

    # Secret key path (used by Odra CLI via .env in cli_project_dir)
    agent_secret_key_path: str = os.environ.get(
        "AGENT_SECRET_KEY_PATH",
        "/mnt/c/Users/Issachar/Downloads/casper-weather-oracle/keys/secret_key.pem"
    )

    # Confidence below this drops the reading — better to skip than post bad data
    # 6000 bps = 60% | 7000 = 70% | 9000 = 90%
    min_confidence_bps_to_post: int = int(
        os.environ.get("MIN_CONFIDENCE_BPS", "7000")
    )

    # Optional: API keys for weather sources (Open-Meteo needs none)
    primary_weather_api_key: str = os.environ.get("WEATHER_API_KEY", "")
    secondary_weather_api_key: str = os.environ.get("WEATHER_API_KEY_BACKUP", "")


def to_fixed_point(value: float) -> int:
    """Convert a float reading to the on-chain fixed-point integer."""
    return round(value * FP_SCALE)


def from_fixed_point(value_fp: int) -> float:
    return value_fp / FP_SCALE
