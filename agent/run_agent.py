"""
Main entry point for the WeatherOracle autonomous agent.
Stores readings to GitHub JSON file for frontend to fetch.
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
from .github_sync import save_reading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weather-oracle-agent")


def run_once(config: AgentConfig, chain: ChainClient) -> dict:
    results = {}
    tick_time = datetime.now(timezone.utc)
    log.info("=== tick started at %s ===", tick_time.isoformat())

    try:
        readings = fetch_current_readings(config.region)
    except Exception as e:
        log.error("failed to fetch primary readings: %s", e)
        return {"error": str(e)}

    for reading in readings:
        metric_name = METRIC_NAMES[reading.metric]
        secondary = fetch_secondary_check(config.region, reading.metric)
        confidence_bps = score_confidence(reading.metric, reading.value, secondary)

        if confidence_bps < config.min_confidence_bps_to_post:
            log.warning("SKIP %s=%.2f — confidence %d bps below threshold %d bps",
                metric_name, reading.value, confidence_bps, config.min_confidence_bps_to_post)
            results[metric_name] = {"status": "skipped", "value": reading.value, "confidence_bps": confidence_bps}
            continue

        value_fp = to_fixed_point(reading.value)
        try:
            tx_hash = chain.submit_reading(
                metric=reading.metric,
                value_fp=value_fp,
                timestamp=reading.timestamp,
                source_confidence_bps=confidence_bps,
            )
            log.info("POSTED %s=%.2f (fp=%d, confidence=%d bps) → tx: %s",
                metric_name, reading.value, value_fp, confidence_bps, tx_hash)

            # Save to GitHub JSON
            confidence_pct = round((confidence_bps / 10000) * 100)
            save_reading(metric_name, reading.value, confidence_pct)

            results[metric_name] = {"status": "posted", "value": reading.value, "value_fp": value_fp, "confidence_bps": confidence_bps, "tx_hash": tx_hash}
        except RuntimeError as e:
            log.error("FAILED to post %s: %s", metric_name, e)
            results[metric_name] = {"status": "failed", "value": reading.value, "error": str(e)}
        except Exception:
            log.exception("unexpected error posting %s", metric_name)
            results[metric_name] = {"status": "error"}

    log.info("=== tick complete: %s ===", results)
    return results


def run_forever(config: AgentConfig) -> None:
    chain = ChainClient.from_config(config)
    log.info("WeatherOracle agent started\n  region:   %s\n  interval: %ds\n  contract: %s",
        config.region.name, config.poll_interval_seconds, config.contract_hash)
    tick_count = 0
    while True:
        tick_count += 1
        log.info("--- tick #%d ---", tick_count)
        try:
            run_once(config, chain)
        except Exception:
            log.exception("tick #%d failed unexpectedly", tick_count)
        log.info("sleeping %ds...", config.poll_interval_seconds)
        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WeatherOracle autonomous agent")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=None)
    args = parser.parse_args()

    cfg = AgentConfig(region=DEFAULT_REGION)
    if args.interval:
        cfg.poll_interval_seconds = args.interval

    if args.once:
        chain = ChainClient.from_config(cfg)
        results = run_once(cfg, chain)
        log.info("results: %s", results)
        sys.exit(0)
    else:
        run_forever(cfg)
