"""Authoritative scoring rules for NUC accreditation-readiness assessments.

The UI stores normalized criterion responses for backward compatibility, while
this module owns section maxima, percentage conversion and accreditation
classification.  Accreditation status is deliberately independent of the
overall programme percentage and of any machine-learning output.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite


SCORING_POLICY_VERSION = "nuc-core-rules-v2"

ACADEMIC_MATTERS = "Academic Matters"
CORE_CATEGORIES = (
    ACADEMIC_MATTERS,
    "Staffing",
    "Physical Facilities",
    "Library",
)

SECTION_MAX = {
    ACADEMIC_MATTERS: 37.0,
    "Staffing": 35.0,
    "Physical Facilities": 27.0,
    "Library": 18.0,
    "Funding": 3.0,
    "Research and Collaboration": 3.0,
    "Tracer and Employers' Rating": 2.0,
}

TOTAL_MAX_SCORE = sum(SECTION_MAX.values())


def score_percentage(obtained_score: float, maximum_score: float) -> float:
    """Return an unrounded percentage for a valid score pair."""

    if obtained_score is None or maximum_score is None:
        raise ValueError("Score and maximum score are required")
    if not isfinite(float(obtained_score)) or not isfinite(float(maximum_score)):
        raise ValueError("Scores must be finite numbers")
    if maximum_score <= 0:
        raise ValueError("Maximum score must be greater than zero")
    if obtained_score < 0 or obtained_score > maximum_score:
        raise ValueError("Obtained score must be between zero and the maximum")
    return (float(obtained_score) / float(maximum_score)) * 100.0


def format_percentage(obtained_score: float | None, maximum_score: float) -> str:
    """Format a score as a percentage without changing classification inputs."""

    if obtained_score is None:
        return "—"
    return f"{score_percentage(obtained_score, maximum_score):.2f}%"


def section_percentages(section_scores: Mapping[str, float]) -> dict[str, float]:
    """Convert authoritative raw section points to unrounded percentages."""

    missing = [name for name in SECTION_MAX if name not in section_scores]
    if missing:
        raise ValueError(f"Missing section scores: {', '.join(missing)}")
    return {
        name: score_percentage(section_scores[name], maximum)
        for name, maximum in SECTION_MAX.items()
    }


def determine_accreditation_status(
    core_percentages: Mapping[str, float] | Sequence[float],
) -> str:
    """Classify the programme from exactly four unrounded core percentages."""

    if isinstance(core_percentages, Mapping):
        if set(core_percentages) != set(CORE_CATEGORIES):
            raise ValueError("Exactly the four core category scores are required")
        values = [core_percentages[name] for name in CORE_CATEGORIES]
    else:
        values = list(core_percentages)
        if len(values) != 4:
            raise ValueError("Four core category scores are required")

    if any(
        value is None
        or not isinstance(value, (int, float))
        or not isfinite(float(value))
        or not 0 <= float(value) <= 100
        for value in values
    ):
        raise ValueError("Invalid accreditation score")

    if any(value < 60 for value in values):
        return "DENIED"
    if all(value >= 70 for value in values):
        return "FULL"
    return "INTERIM"


def calculate_funding_score(amount: float) -> int:
    """Return funding points using the corrected Naira boundaries.

    The correction specifies that the second band starts at ₦300,000, so that
    value is the implemented boundary.  Zero is a valid amount and receives one
    point, as it is within the stated below-₦300,000 band.
    """

    if amount is None or not isinstance(amount, (int, float)):
        raise ValueError("Invalid funding amount")
    if not isfinite(float(amount)) or amount < 0:
        raise ValueError("Invalid funding amount")
    if amount < 300_000:
        return 1
    if amount < 1_000_000:
        return 2
    return 3


def funding_band(amount: float) -> tuple[str, int]:
    points = calculate_funding_score(amount)
    labels = {
        1: "Below ₦300,000",
        2: "₦300,000 to below ₦1,000,000",
        3: "₦1,000,000 and above",
    }
    return labels[points], points
