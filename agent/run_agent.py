"""
Main entry point for the WeatherOracle autonomous agent.

Run modes:
  python -m agent.run_agent          → runs forever, posts every POLL_INTERVAL_SECONDS
  python -m agent.run_agent --once   → single tick then exit (good for testing)

Environment variables (set in .env or shell):
  POLL_INTERVAL_SECONDS   How often to post readings (default: 300 = 5 minutes)
  ORACLE_CONTRACT_HASH    WeatherOracle contract package hash
  CASPER_NODE_URL         RPC node URL (default: http://65.109.89.88:7777)
  CLI_PROJECT_DIR         Path to contracts/weather_oracle_new (where cargo lives)
  MIN_CONFIDENCE_BPS      Minimum confidence to post (default: 7000 = 70%)
"""
import argparse
import logging
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from .config import AgentConfig, DEFAULT_REGION, to_fixed_point, METRIC_NAMES
from .weather_source import fetch_current_readings, fetch_secondary_check
from .confidence import score_confidence
from .chain_client import ChainClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weather-oracle-agent")


def run_once(config: AgentConfig, chain: ChainClient) -> dict:
    """
    One full scheduler tick — fetch all three metrics, score each,
    post the ones that clear the confidence threshold.

    Returns a summary dict with results for each metric.
    """
    results = {}
    tick_time = datetime.now(timezone.utc)
    log.info("=== tick started at %s ===", tick_time.isoformat())

    # Fetch primary readings
    try:
        readings = fetch_current_readings(config.region)
    except Exception as e:
        log.error("failed to fetch primary readings: %s", e)
        return {"error": str(e)}

    for reading in readings:
        metric_name = METRIC_NAMES[reading.metric]

        # Fetch secondary for confidence scoring
        secondary = fetch_secondary_check(config.region, reading.metric)

        # Score confidence
        confidence_bps = score_confidence(
            reading.metric, reading.value, secondary
        )

        if confidence_bps < config.min_confidence_bps_to_post:
            log.warning(
                "SKIP %s=%.2f — confidence %d bps below threshold %d bps",
                metric_name, reading.value,
                confidence_bps, config.min_confidence_bps_to_post,
            )
            results[metric_name] = {
                "status": "skipped",
                "value": reading.value,
                "confidence_bps": confidence_bps,
            }
            continue

        # Post on-chain
        value_fp = to_fixed_point(reading.value)
        try:
            tx_hash = chain.submit_reading(
                metric=reading.metric,
                value_fp=value_fp,
                timestamp=reading.timestamp,
                source_confidence_bps=confidence_bps,
            )
            log.info(
                "POSTED %s=%.2f (fp=%d, confidence=%d bps) → tx: %s",
                metric_name, reading.value, value_fp, confidence_bps, tx_hash,
            )
            results[metric_name] = {
                "status": "posted",
                "value": reading.value,
                "value_fp": value_fp,
                "confidence_bps": confidence_bps,
                "tx_hash": tx_hash,
            }
        except RuntimeError as e:
            log.error("FAILED to post %s: %s", metric_name, e)
            results[metric_name] = {
                "status": "failed",
                "value": reading.value,
                "error": str(e),
            }
        except Exception:
            log.exception("unexpected error posting %s", metric_name)
            results[metric_name] = {"status": "error"}

    log.info("=== tick complete: %s ===", results)
    return results


def run_forever(config: AgentConfig) -> None:
    """Runs the agent loop indefinitely."""
    chain = ChainClient.from_config(config)

    log.info(
        "WeatherOracle agent started\n"
        "  region:   %s (%.4f, %.4f)\n"
        "  interval: %ds (every %.1f minutes)\n"
        "  contract: %s\n"
        "  min conf: %d bps (%.0f%%)",
        config.region.name,
        config.region.latitude,
        config.region.longitude,
        config.poll_interval_seconds,
        config.poll_interval_seconds / 60,
        config.contract_hash,
        config.min_confidence_bps_to_post,
        config.min_confidence_bps_to_post / 100,
    )

    tick_count = 0
    while True:
        tick_count += 1
        log.info("--- tick #%d ---", tick_count)
        try:
            run_once(config, chain)
        except Exception:
            log.exception("tick #%d failed unexpectedly", tick_count)

        log.info(
            "sleeping %ds until next tick...",
            config.poll_interval_seconds
        )
        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WeatherOracle autonomous agent")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single tick and exit (useful for testing)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override poll interval in seconds"
    )
    args = parser.parse_args()

    cfg = AgentConfig(region=DEFAULT_REGION)
    if args.interval:
        cfg.poll_interval_seconds = args.interval

    if args.once:
        log.info("running single tick (--once mode)")
        chain = ChainClient.from_config(cfg)
        results = run_once(cfg, chain)
        log.info("results: %s", results)
        sys.exit(0)
    else:
        run_forever(cfg)
