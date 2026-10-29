import math

import pytest

from assessment_rules import (
    ACADEMIC_MATTERS,
    CORE_CATEGORIES,
    SECTION_MAX,
    TOTAL_MAX_SCORE,
    calculate_funding_score,
    determine_accreditation_status,
    format_percentage,
    score_percentage,
)


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ([85, 90, 80, 75], "FULL"),
        ([75, 82, 65, 76], "INTERIM"),
        ([90, 85, 56.67, 80], "DENIED"),
        ([70, 70, 70, 70], "FULL"),
        ([69.99, 80, 85, 90], "INTERIM"),
        ([59.99, 90, 90, 90], "DENIED"),
        ([60, 60, 60, 60], "INTERIM"),
    ],
)
def test_accreditation_classification_boundaries(scores, expected):
    assert determine_accreditation_status(scores) == expected


def test_mapping_requires_exactly_the_four_core_categories():
    scores = dict(zip(CORE_CATEGORIES, [85, 90, 80, 75]))
    assert determine_accreditation_status(scores) == "FULL"

    scores["Funding"] = 100
    with pytest.raises(ValueError, match="Exactly the four"):
        determine_accreditation_status(scores)


@pytest.mark.parametrize("scores", [[], [70] * 3, [70] * 5])
def test_classification_rejects_wrong_number_of_scores(scores):
    with pytest.raises(ValueError, match="Four core"):
        determine_accreditation_status(scores)


@pytest.mark.parametrize(
    "scores",
    [
        [None, 70, 70, 70],
        [-0.01, 70, 70, 70],
        [100.01, 70, 70, 70],
        [math.nan, 70, 70, 70],
        [math.inf, 70, 70, 70],
    ],
)
def test_classification_rejects_invalid_scores(scores):
    with pytest.raises(ValueError, match="Invalid accreditation score"):
        determine_accreditation_status(scores)


def test_classification_uses_unrounded_percentage():
    raw_academic_points = 22.19963  # 59.999% of 37, displayed as 60.00%
    unrounded = score_percentage(raw_academic_points, SECTION_MAX[ACADEMIC_MATTERS])

    assert f"{unrounded:.2f}%" == "60.00%"
    assert determine_accreditation_status([unrounded, 90, 90, 90]) == "DENIED"


def test_high_programme_total_cannot_override_failed_core_category():
    # Non-core categories can lift the programme total, but Facilities below 60
    # must still produce DENIED.
    core = [100, 100, 59.99, 100]
    assert determine_accreditation_status(core) == "DENIED"


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0, 1),
        (299_999, 1),
        (300_000, 2),
        (999_999, 2),
        (1_000_000, 3),
    ],
)
def test_funding_boundaries(amount, expected):
    assert calculate_funding_score(amount) == expected


@pytest.mark.parametrize("amount", [None, -1, math.nan, math.inf])
def test_funding_rejects_invalid_amount(amount):
    with pytest.raises(ValueError, match="Invalid funding amount"):
        calculate_funding_score(amount)


def test_section_maxima_include_corrected_tracer_denominator():
    assert SECTION_MAX["Tracer and Employers' Rating"] == 2
    assert TOTAL_MAX_SCORE == 125


def test_percentage_formatting_is_consistent():
    assert score_percentage(25.08, 37) == pytest.approx(67.7837837838)
    assert format_percentage(25.08, 37) == "67.78%"
    assert format_percentage(None, 37) == "—"
