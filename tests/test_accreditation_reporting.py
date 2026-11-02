import re

from accreditation_reporting import CRITERION_RULES, build_deterministic_report, generate_findings
from assessment_rules import ACADEMIC_MATTERS, SECTION_MAX, determine_accreditation_status


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
    expected = {
        "curriculum_aligned_with_BMAS", "innovative_courses_present",
        "curriculum_coverage_complete", "admission_requirements_compliant",
        "academic_regulations_defined", "tests_and_examinations_standardized",
        "evaluation_methods_clear", "degree_projects_adequate",
        "practical_work_adequate", "student_course_evaluation_present",
        "skills_acquisition_programme", "external_examiner_system",
        "internal_quality_assurance", "staff_student_ratio_compliant",
        "proportion_core_staff_sufficient", "staff_rank_mix_balanced",
        "academic_staff_qualification_high", "staff_competence_verified",
        "administrative_support_available", "non_teaching_staff_adequate",
        "academic_staff_development_programme",
        "non_academic_staff_development_programme", "laboratory_space_adequate",
        "laboratory_equipment_adequate", "classroom_space_adequate",
        "classroom_equipment_adequate", "office_accommodation_adequate",
        "safety_environment_present", "library_holdings_adequate",
        "library_material_current", "e_library_subscription_available",
        "e_library_access_good", "programme_funding_adequate",
        "research_collaboration_active", "employer_rating_positive",
    }
    assert expected <= CRITERION_RULES.keys()
