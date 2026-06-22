"""
Reconciliation job: run this on a slower cadence (e.g. daily) than the
main agent. It re-fetches the official value for a past reading from a
slower-but-more-authoritative source and calls `record_outcome` on the
Reputation contract, which is what actually moves the public accuracy
score your dashboard shows.

Kept as a separate script (not folded into run_agent.py) because in a
real deployment you may want this triggered by a different schedule, or
even run by a different wallet than the one posting live readings —
splitting "post" and "grade" privileges is a reasonable trust boundary
even though the MVP can run both from the same key for simplicity.
"""
import logging

from .config import AgentConfig, DEFAULT_REGION, to_fixed_point
from .chain_client import ChainClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("weather-oracle-reconciler")


def fetch_official_value(metric: int, timestamp: int) -> float:
    """
    Placeholder: pull the authoritative historical value for this metric
    and timestamp. For a real run, this should hit an archival weather
    API (e.g. NOAA's historical observations endpoint) rather than the
    same live forecast API the agent used — reconciliation only means
    something if it's checked against an independent source.
    """
    raise NotImplementedError(
        "Wire this up to a historical/archival weather data source "
        "before running reconciliation for real."
    )


def reconcile_reading(
    chain: ChainClient,
    reading_index: int,
    metric: int,
    posted_value_fp: int,
    timestamp: int,
) -> None:
    official_value = fetch_official_value(metric, timestamp)
    official_value_fp = to_fixed_point(official_value)

    # NOTE: mirrors the same "confirm exact pycspr call shape" caveat as
    # ChainClient.submit_reading — record_outcome needs the same
    # stored-contract-call pattern, just against the Reputation contract
    # hash and entry point instead of WeatherOracle's.
    log.info(
        "reconciling reading #%d: posted=%d official=%d",
        reading_index,
        posted_value_fp,
        official_value_fp,
    )
    # chain.record_outcome(reading_index, posted_value_fp, official_value_fp)


if __name__ == "__main__":
    cfg = AgentConfig(region=DEFAULT_REGION)
    chain_client = ChainClient.from_config(cfg)
    log.info("reconciliation job scaffold ready — implement fetch_official_value first")
