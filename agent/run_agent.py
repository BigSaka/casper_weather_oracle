"""
Main entry point for the weather oracle agent.

Run as a long-lived process (`python -m agent.run_agent`) or invoke
`run_once()` from a cron job / scheduled cloud function — either works,
the loop itself is stateless between ticks.
"""
import logging
import time

from .config import AgentConfig, DEFAULT_REGION, to_fixed_point, METRIC_NAMES
from .weather_source import fetch_current_readings, fetch_secondary_check
from .confidence import score_confidence
from .chain_client import ChainClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("weather-oracle-agent")


def run_once(config: AgentConfig, chain: ChainClient) -> None:
    """One full scheduler tick: fetch all three metrics, score each, post
    the ones that clear the confidence bar."""
    readings = fetch_current_readings(config.region)
    log.info("fetched %d raw readings for %s", len(readings), config.region.name)

    for reading in readings:
        secondary = fetch_secondary_check(config.region, reading.metric)
        confidence_bps = score_confidence(reading.metric, reading.value, secondary)
        metric_name = METRIC_NAMES[reading.metric]

        if confidence_bps < config.min_confidence_bps_to_post:
            log.warning(
                "skipping %s: confidence %d bps below threshold %d bps",
                metric_name,
                confidence_bps,
                config.min_confidence_bps_to_post,
            )
            continue

        value_fp = to_fixed_point(reading.value)
        try:
            deploy_hash = chain.submit_reading(
                metric=reading.metric,
                value_fp=value_fp,
                timestamp=reading.timestamp,
                source_confidence_bps=confidence_bps,
            )
            log.info(
                "posted %s=%.2f (confidence %d bps) -> deploy %s",
                metric_name,
                reading.value,
                confidence_bps,
                deploy_hash,
            )
        except Exception:
            log.exception("failed to submit %s reading", metric_name)


def run_forever(config: AgentConfig) -> None:
    chain = ChainClient.from_config(config)
    log.info(
        "agent started, region=%s, interval=%ds, contract=%s",
        config.region.name,
        config.poll_interval_seconds,
        config.contract_hash,
    )
    while True:
        try:
            run_once(config, chain)
        except Exception:
            log.exception("tick failed, will retry next interval")
        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    cfg = AgentConfig(region=DEFAULT_REGION)
    run_forever(cfg)
