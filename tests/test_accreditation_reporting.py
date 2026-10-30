from accreditation_reporting import build_deterministic_report, generate_findings
from assessment_rules import ACADEMIC_MATTERS, SECTION_MAX, determine_accreditation_status


def complete_scores(core_percentage=80.0):
    scores = {name: maximum for name, maximum in SECTION_MAX.items()}
    for category in (ACADEMIC_MATTERS, "Staffing", "Physical Facilities", "Library"):
        scores[category] = SECTION_MAX[category] * core_percentage / 100
    return scores


def test_fully_compliant_programme_has_accurate_empty_state():
    scores = complete_scores(80)
    responses = {category: {"verified_criterion": 1.0} for category in SECTION_MAX}
    findings = generate_findings(scores, responses)
    status = determine_accreditation_status([80, 80, 80, 80])
    report = build_deterministic_report(
        institution="Test University",
        discipline="Computing",
        programme="Computer Science",
        programme_score=80,
        accreditation_status=status,
        section_scores=scores,
        findings=findings,
    )

    assert findings == []
    assert "FULL ACCREDITATION" in report
    assert "No deficiencies were identified" in report
    assert "Deficiencies and Recommended Remedies" in report


def test_denied_report_identifies_one_failed_core_area():
    scores = complete_scores(80)
    scores["Physical Facilities"] = SECTION_MAX["Physical Facilities"] * 0.55
    findings = generate_findings(scores, {})

    assert any(
        finding.category == "Physical Facilities"
        and finding.priority == "Critical"
        and "triggers denied accreditation" in finding.deficiency
        for finding in findings
    )


def test_multiple_failed_core_areas_are_all_reported():
    scores = complete_scores(80)
    scores[ACADEMIC_MATTERS] = SECTION_MAX[ACADEMIC_MATTERS] * 0.50
    scores["Library"] = SECTION_MAX["Library"] * 0.59

    findings = generate_findings(scores, {})
    failed_categories = {
        finding.category
        for finding in findings
        if finding.criterion == "Core category performance"
    }
    assert failed_categories == {ACADEMIC_MATTERS, "Library"}


def test_interim_report_uses_70_percent_gap_without_claiming_denial():
    scores = complete_scores(80)
    scores["Staffing"] = SECTION_MAX["Staffing"] * 0.65
    findings = generate_findings(scores, {})

    staffing = next(item for item in findings if item.category == "Staffing")
    assert staffing.priority == "High"
    assert "full-accreditation threshold" in staffing.deficiency


def test_missing_evidence_is_reported_as_unknown_not_noncompliance():
    scores = complete_scores(80)
    findings = generate_findings(
        scores,
        {ACADEMIC_MATTERS: {"external_examiner_evidence": None}},
    )

    finding = findings[0]
    assert finding.observed_performance == "No response recorded"
    assert "cannot be determined" in finding.deficiency


def test_zero_and_incomplete_records_generate_safe_findings():
    scores = complete_scores(0)
    findings = generate_findings(scores, {"Library": {"holdings": None}})

    assert len(findings) >= 5
    assert any(item.observed_performance == "0.00%" for item in findings)
    assert any(item.observed_performance == "No response recorded" for item in findings)


def test_report_generation_is_repeatable_and_external_api_independent():
    scores = complete_scores(65)
    findings = generate_findings(scores, {})
    kwargs = dict(
        institution="Test University",
        discipline="Science",
        programme="Physics",
        programme_score=71.25,
        accreditation_status="INTERIM",
        section_scores=scores,
        findings=findings,
    )

    first = build_deterministic_report(**kwargs)
    second = build_deterministic_report(**kwargs)

    assert first == second
    assert "INTERIM ACCREDITATION" in first
    assert "Programme score:** 71.25%" in first
    assert "OpenAI" not in first
