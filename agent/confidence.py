"""
Confidence scoring: turns a primary reading (and, if available, a
secondary cross-check) into a basis-points confidence score the contract
can use to decide whether a reading is trustworthy enough to act on.

This is intentionally simple for the MVP — the point for the buildathon
demo is that the agent does *some* verification work before writing
on-chain, not that the scoring model is sophisticated. A natural next
step is replacing `score_confidence` with a small model that also
weighs recent historical accuracy (from the Reputation contract) into
the score.
"""
from typing import Optional

# How close two sources need to be (in source units, not fixed-point) to
# count as full agreement. Loosened per metric since their natural scales
# differ wildly (mm of rain vs km/h vs degrees C).
AGREEMENT_TOLERANCE = {
    0: 2.0,   # rainfall mm
    1: 5.0,   # wind speed km/h
    2: 1.5,   # temperature C
}

NO_SECONDARY_SOURCE_CONFIDENCE_BPS = 7000  # 70%, moderate trust
FULL_AGREEMENT_CONFIDENCE_BPS = 9800
MAX_DISAGREEMENT_CONFIDENCE_BPS = 3000


def score_confidence(
    metric: int,
    primary_value: float,
    secondary_value: Optional[float],
) -> int:
    """Returns a confidence score in basis points (0-10000)."""
    if secondary_value is None:
        return NO_SECONDARY_SOURCE_CONFIDENCE_BPS

    tolerance = AGREEMENT_TOLERANCE.get(metric, 5.0)
    diff = abs(primary_value - secondary_value)

    if diff <= tolerance:
        return FULL_AGREEMENT_CONFIDENCE_BPS

    # Linearly decay confidence as disagreement grows, floor at the
    # "max disagreement" value rather than zero — a single noisy tick
    # shouldn't fully zero out trust.
    decay_range_bps = FULL_AGREEMENT_CONFIDENCE_BPS - MAX_DISAGREEMENT_CONFIDENCE_BPS
    # Disagreement beyond 5x tolerance is treated as maximally unreliable.
    overshoot = min(diff / (tolerance * 5), 1.0)
    return int(FULL_AGREEMENT_CONFIDENCE_BPS - decay_range_bps * overshoot)
