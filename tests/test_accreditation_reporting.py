import ast
import re
from pathlib import Path

import pytest

from accreditation_reporting import CRITERION_RULES, build_deterministic_report, generate_findings
from assessment_rules import ACADEMIC_MATTERS, SECTION_MAX, determine_accreditation_status


APP_SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def active_questionnaire_criterion_ids():
    """Derive reportable IDs from the active New Assessment response graph."""

    tree = ast.parse(APP_SOURCE)
    new_assessment = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and any(
            isinstance(part, ast.Constant) and part.value == "New Assessment"
            for part in ast.walk(node.test)
        )
    )

    assignments = {}
    criterion_responses = None
    for node in ast.walk(new_assessment):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        assignments[target.id] = node.value
        if target.id == "criterion_responses":
            criterion_responses = node.value

    assert isinstance(criterion_responses, ast.Dict), (
        "The active assessment must expose criterion_responses as a dictionary "
        "so reporting coverage can be audited."
    )

    def dict_keys(value):
        if isinstance(value, ast.Name):
            assert value.id in assignments, f"Unresolved questionnaire response group: {value.id}"
            return dict_keys(assignments[value.id])
        assert isinstance(value, ast.Dict), (
            "Questionnaire response groups must remain statically auditable dictionaries; "
            f"unsupported expression: {ast.dump(value, include_attributes=False)}"
        )
        keys = []
        for key in value.keys:
            assert isinstance(key, ast.Constant) and isinstance(key.value, str), (
                "Questionnaire criterion IDs must be string literals."
            )
            keys.append(key.value)
        return keys

    criterion_ids = set()
    for response_group in criterion_responses.values:
        criterion_ids.update(dict_keys(response_group))
    return criterion_ids


def complete_scores(core_percentage=80.0):
    scores = {name: maximum for name, maximum in SECTION_MAX.items()}
    for category in (ACADEMIC_MATTERS, "Staffing", "Physical Facilities", "Library"):
        scores[category] = SECTION_MAX[category] * core_percentage / 100
    return scores


def build_report(findings, status="FULL"):
    return build_deterministic_report(
        institution="Test University",
        discipline="Computing",
        programme="Computer Science",
        programme_score=91.25,
        accreditation_status=status,
        section_scores=complete_scores(),
        findings=findings,
        assessment_date="2026-10-30",
    )


def test_fully_compliant_programme_has_accurate_empty_state():
    scores = complete_scores(80)
    responses = {category: {"verified_criterion": 1.0} for category in SECTION_MAX}
    findings = generate_findings(scores, responses)
    report = build_report(findings)

    assert findings == []
    assert "FULL ACCREDITATION" in report
    assert "No substantiated deficiencies were identified" in report
    assert "official accreditation" not in report


def test_report_has_exact_four_section_sequence_and_no_scores():
    report = build_report([], status="INTERIM")
    headings = re.findall(r"^## (.+)$", report, flags=re.MULTILINE)

    assert headings == [
        "Accreditation Status",
        "Accreditation Assessment Summary",
        "Deficiencies",
        "Remedies",
    ]
    assert "30 October 2026" in report
    assert "Programme score" not in report
    assert "91.25" not in report
    assert "Core Accreditation Performance" not in report
    assert "Advisory Disclaimer" not in report
    assert "%" not in report


def test_failed_philosophy_and_objectives_is_reported_above_aggregate_threshold():
    findings = generate_findings(
        complete_scores(80),
        {ACADEMIC_MATTERS: {"philosophy_objectives_defined": 0.0}},
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding.criterion == "Philosophy and objectives"
    assert finding.source_criterion_ids == ("philosophy_objectives_defined",)
    assert finding.deficiency == (
        "The programme philosophy and objectives do not meet the applicable "
        "CCMAS statement-and-alignment criterion."
    )
    assert finding.remedy == (
        "The institution should revise and formally document the programme philosophy "
        "and objectives to align with the applicable CCMAS requirements."
    )

    report = build_report(findings)
    headings = re.findall(r"^## (.+)$", report, flags=re.MULTILINE)
    assert headings == [
        "Accreditation Status",
        "Accreditation Assessment Summary",
        "Deficiencies",
        "Remedies",
    ]
    assert finding.deficiency in report
    assert finding.remedy in report


def test_compliant_philosophy_and_objectives_has_no_false_deficiency():
    findings = generate_findings(
        complete_scores(80),
        {ACADEMIC_MATTERS: {"philosophy_objectives_defined": 1.0}},
    )

    assert not any(
        "philosophy_objectives_defined" in finding.source_criterion_ids
        for finding in findings
    )


def test_missing_philosophy_response_remains_distinct_from_confirmed_deficiency():
    findings = generate_findings(
        complete_scores(80),
        {ACADEMIC_MATTERS: {"philosophy_objectives_defined": None}},
    )

    assert len(findings) == 1
    assert findings[0].observed_performance == "No response recorded"
    assert "cannot be determined" in findings[0].deficiency
    assert "not well stated" not in findings[0].deficiency


def test_library_weaknesses_are_specific_and_meaningfully_consolidated():
    findings = generate_findings(
        complete_scores(),
        {
            "Library": {
                "library_holdings_adequate": 0.5,
                "library_material_current": 0.25,
                "e_library_subscription_available": 1.0,
                "e_library_access_good": 1.0,
            }
        },
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "Library"
    assert set(finding.source_criterion_ids) == {
        "library_holdings_adequate",
        "library_material_current",
    }
    assert "library holdings" in finding.deficiency.lower()
    assert "current" in finding.deficiency.lower()
    assert "procure" in finding.remedy.lower()


def test_nonmaximum_satisfactory_response_is_not_automatically_a_deficiency():
    findings = generate_findings(
        complete_scores(),
        {"Library": {"library_holdings_adequate": 0.75}},
    )
    assert findings == []


def test_multiple_categories_and_each_remedy_correspond_by_number():
    responses = {
        "Staffing": {"staff_student_ratio_compliant": 0.5},
        "Physical Facilities": {"laboratory_equipment_adequate": 0.5},
        "Funding": {"programme_funding_adequate": 1 / 3},
        "Tracer and Employers' Rating": {"employer_rating_positive": 0.5},
    }
    findings = generate_findings(complete_scores(), responses)
    report = build_report(findings, status="DENIED")

    assert {item.category for item in findings} == set(responses)
    deficiencies = report.split("## Deficiencies", 1)[1].split("## Remedies", 1)[0]
    remedies = report.split("## Remedies", 1)[1]
    assert re.findall(r"(?m)^(\d+)\. ", deficiencies) == ["1", "2", "3", "4"]
    assert re.findall(r"(?m)^(\d+)\. ", remedies) == ["1", "2", "3", "4"]
    assert "academic staff" in deficiencies.lower()
    assert "equipment" in deficiencies.lower()
    assert "funding" in deficiencies.lower()
    assert "tracer" in remedies.lower()


def test_missing_response_is_unknown_not_fabricated_noncompliance():
    findings = generate_findings(
        complete_scores(),
        {ACADEMIC_MATTERS: {"external_examiner_system": None}},
    )

    assert len(findings) == 1
    assert findings[0].observed_performance == "No response recorded"
    assert "cannot be determined" in findings[0].deficiency
    assert "provide and verify" in findings[0].remedy


def test_category_fallback_is_professional_when_only_aggregate_evidence_exists():
    scores = complete_scores()
    scores["Physical Facilities"] = SECTION_MAX["Physical Facilities"] * 0.55
    findings = generate_findings(scores, {})

    facility = next(item for item in findings if item.category == "Physical Facilities")
    assert "facilities are inadequate" in facility.deficiency
    assert "70%" not in facility.deficiency
    assert "lowest-scoring" not in facility.remedy


def test_classification_remains_independent_of_public_report_content():
    assert determine_accreditation_status([70, 70, 70, 70]) == "FULL"
    assert determine_accreditation_status([60, 70, 70, 70]) == "INTERIM"
    assert determine_accreditation_status([59.999, 100, 100, 100]) == "DENIED"


def test_report_generation_is_repeatable_and_external_api_independent():
    findings = generate_findings(complete_scores(65), {})
    first = build_report(findings, status="INTERIM")
    second = build_report(findings, status="INTERIM")

    assert first == second
    assert "INTERIM ACCREDITATION" in first
    assert "OpenAI" not in first


def test_finding_rules_cover_every_supported_manual_assessment_criterion():
    active_criteria = active_questionnaire_criterion_ids()
    unmapped = active_criteria - CRITERION_RULES.keys()

    assert "philosophy_objectives_defined" in active_criteria
    assert not unmapped, f"Active questionnaire criteria without reporting rules: {sorted(unmapped)}"


def test_no_graduates_report_explains_tracer_applicability_without_a_deficiency():
    note = (
        "Not Yet Assessable because the programme has not graduated students. "
        "Supervised industrial experience was assessed separately."
    )
    findings = generate_findings(
        complete_scores(),
        {"Tracer and Employers' Rating": {"supervised_industrial_experience": 1.0}},
    )
    report = build_deterministic_report(
        institution="Test University",
        discipline="Computing",
        programme="Computer Science",
        accreditation_status="FULL",
        findings=findings,
        assessment_date="2026-11-14",
        tracer_applicability_note=note,
    )

    assert findings == []
    assert note in report
    assert "Graduate tracer assessment" in report
    assert "graduate tracer system" not in report.lower()


def test_industrial_experience_findings_follow_selected_rating():
    average = generate_findings(
        complete_scores(),
        {"Tracer and Employers' Rating": {"supervised_industrial_experience": 0.5}},
    )
    below_average = generate_findings(
        complete_scores(),
        {"Tracer and Employers' Rating": {"supervised_industrial_experience": 0.0}},
    )

    assert len(average) == 1
    assert "rated Average" in average[0].deficiency
    assert "above Average" in average[0].remedy
    assert len(below_average) == 1
    assert "rated Below average" in below_average[0].deficiency
    assert "below-average performance" in below_average[0].remedy


def test_degree_project_deficiency_does_not_invent_unselected_weaknesses():
    findings = generate_findings(
        complete_scores(),
        {ACADEMIC_MATTERS: {"degree_projects_adequate": 0.5}},
    )

    assert len(findings) == 1
    assert findings[0].deficiency == (
        "Degree projects are innovative and creative but are not adequately supervised."
    )
    assert "relevance" not in findings[0].deficiency.lower()
    assert "quality" not in findings[0].deficiency.lower()
    assert "supervis" in findings[0].remedy.lower()


@pytest.mark.parametrize(
    ("score", "expected", "unexpected"),
    [
        (0.66, "does not adequately cover", "quality standard"),
        (0.33, "does not meet the required quality", "curriculum coverage"),
        (0.0, "is not conducted", "quality, depth"),
    ],
)
def test_practical_work_deficiency_matches_exact_response(score, expected, unexpected):
    findings = generate_findings(
        complete_scores(),
        {ACADEMIC_MATTERS: {"practical_work_adequate": score}},
    )

    assert len(findings) == 1
    assert expected in findings[0].deficiency
    assert unexpected not in findings[0].deficiency


def test_facility_findings_remain_separate_and_response_specific():
    findings = generate_findings(
        complete_scores(),
        {
            "Physical Facilities": {
                "laboratory_space_adequate": 0.66,
                "laboratory_equipment_adequate": 0.5,
                "classroom_equipment_adequate": 0.5,
                "office_accommodation_adequate": 0.66,
            }
        },
    )

    assert len(findings) == 4
    by_criterion = {finding.criterion: finding for finding in findings}
    practical_space = by_criterion["Laboratory and practical space"]
    laboratory_equipment = by_criterion["Laboratory equipment"]
    assert practical_space.deficiency == (
        "Available practical space does not meet the applicable NUC standard."
    )
    assert practical_space.remedy == (
        "The institution should provide adequate practical space that meets the applicable NUC standard."
    )
    assert laboratory_equipment.deficiency == (
        "Laboratory equipment does not meet the applicable NUC standard."
    )
    assert laboratory_equipment.remedy == (
        "The institution should provide adequate laboratory equipment that meets the applicable NUC requirements."
    )
    for finding in (practical_space, laboratory_equipment):
        assert "%" not in finding.deficiency
        assert "%" not in finding.remedy
    assert "partially meets" in by_criterion["Classroom equipment"].deficiency
    assert by_criterion["Office accommodation"].deficiency == (
        "Office accommodation is well equipped but slightly inadequate in space."
    )


@pytest.mark.parametrize("score", [1 / 3, 2 / 3])
def test_funding_finding_is_concise_and_does_not_expose_bands(score):
    findings = generate_findings(
        complete_scores(),
        {"Funding": {"programme_funding_adequate": score}},
    )

    assert len(findings) == 1
    assert findings[0].deficiency == "Programme funding is inadequate."
    assert findings[0].remedy == "The programme should be adequately funded."
    assert "₦" not in findings[0].deficiency
    assert "₦" not in findings[0].remedy


def test_markdown_report_uses_corrected_non_numerical_findings():
    findings = generate_findings(
        complete_scores(),
        {
            "Physical Facilities": {
                "laboratory_space_adequate": 0.0,
                "laboratory_equipment_adequate": 0.0,
            },
            "Funding": {"programme_funding_adequate": 2 / 3},
        },
    )
    report = build_deterministic_report(
        institution="Test University",
        discipline="Computing",
        programme="Computer Science",
        accreditation_status="INTERIM",
        findings=findings,
        assessment_date="2026-11-15",
    )

    assert "Programme funding is inadequate." in report
    assert "The programme should be adequately funded." in report
    assert "Available practical space does not meet the applicable NUC standard." in report
    assert "Laboratory equipment does not meet the applicable NUC standard." in report
    assert "₦300,000" not in report
    assert "50%" not in report
    assert "70%" not in report


def test_curriculum_combination_is_one_supported_statement_not_two_guesses():
    findings = generate_findings(
        complete_scores(),
        {
            ACADEMIC_MATTERS: {
                "curriculum_aligned_with_BMAS": 0.0,
                "curriculum_coverage_complete": 0.0,
            }
        },
    )

    assert len(findings) == 1
    assert findings[0].deficiency.count(".") == 1
    assert "including the required curriculum coverage" in findings[0].deficiency
