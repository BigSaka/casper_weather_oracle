"""
Confidence scoring for weather readings.

Takes a primary reading and an optional secondary reading from a different
source and returns a confidence score in basis points (0-10000).

Scoring logic:
- No secondary source available → 6500 bps (65%) — moderate confidence
- Sources agree within 5% tolerance → 9500 bps (95%) — high confidence  
- Sources agree within 10% tolerance → 8000 bps (80%) — good confidence
- Sources agree within 20% tolerance → 7000 bps (70%) — acceptable
- Sources disagree beyond 20% → 4000 bps (40%) — below posting threshold

For zero/near-zero values (e.g. 0mm rainfall), we use absolute difference
instead of percentage to avoid division-by-zero issues.
"""
import logging
from typing import Optional

log = logging.getLogger("weather-oracle-agent.confidence")

# Absolute tolerance for near-zero values
NEAR_ZERO_THRESHOLD = 0.5


def score_confidence(
    metric: int,
    primary_value: float,
    secondary_value: Optional[float],
) -> int:
    """
    Returns confidence in basis points (0-10000).
    10000 bps = 100% confidence, 7000 bps = 70%, etc.
    """
    if secondary_value is None:
        log.debug("metric %d: no secondary source, returning moderate confidence", metric)
        return 6500

    # Use absolute difference for near-zero values
    if abs(primary_value) < NEAR_ZERO_THRESHOLD:
        abs_diff = abs(primary_value - secondary_value)
        if abs_diff < NEAR_ZERO_THRESHOLD:
            confidence = 9500
        elif abs_diff < NEAR_ZERO_THRESHOLD * 2:
            confidence = 8000
        else:
            confidence = 4000
        log.debug(
            "metric %d: near-zero values primary=%.2f secondary=%.2f "
            "abs_diff=%.2f → %d bps",
            metric, primary_value, secondary_value, abs_diff, confidence
        )
        return confidence

    # Percentage difference for normal values
    pct_diff = abs(primary_value - secondary_value) / abs(primary_value)

    if pct_diff <= 0.05:
        confidence = 9500   # within 5% — excellent agreement
    elif pct_diff <= 0.10:
        confidence = 8000   # within 10% — good agreement
    elif pct_diff <= 0.20:
        confidence = 7000   # within 20% — acceptable
    else:
        confidence = 4000   # beyond 20% — sources disagree, skip

    log.info(
        "metric %d: primary=%.2f secondary=%.2f pct_diff=%.1f%% → %d bps confidence",
        metric, primary_value, secondary_value, pct_diff * 100, confidence
    )
    return confidence
