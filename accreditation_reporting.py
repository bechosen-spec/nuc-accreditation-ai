"""Deterministic, evidence-grounded accreditation readiness reporting.

The scoring engine and public report are deliberately separate. Scores remain
available to classification and persistence, while this module converts
recorded criterion responses into concise findings and renders the same
four-section report for the UI and Markdown download.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Mapping

from assessment_rules import CORE_CATEGORIES, SECTION_MAX, score_percentage


@dataclass(frozen=True)
class CriterionRule:
    label: str
    group: str
    deficiency: str
    remedy: str
    minimum_normalized_score: float = 0.70


@dataclass(frozen=True)
class Finding:
    id: str
    category: str
    criterion: str
    deficiency: str
    remedy: str
    source_criterion_ids: tuple[str, ...]
    observed_performance: str = "Recorded assessment response indicates a weakness"
    expected_standard: str = "A satisfactory response under the configured assessment rubric"
    priority: str = "High"
    timeframe: str = "As part of the programme improvement plan"

    @property
    def recommended_action(self) -> str:
        """Backward-compatible name used by older payload consumers."""

        return self.remedy

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["source_criterion_ids"] = list(self.source_criterion_ids)
        record["recommended_action"] = self.remedy
        return record


def _rule(label: str, group: str, deficiency: str, remedy: str) -> CriterionRule:
    return CriterionRule(label, group, deficiency, remedy)


CRITERION_RULES: dict[str, CriterionRule] = {
    # Academic Matters
    "philosophy_objectives_defined": _rule(
        "Philosophy and objectives",
        "academic_governance",
        "The programme philosophy and objectives are not well stated or are not aligned with the applicable CCMAS requirements.",
        "The institution should revise and formally document the programme philosophy and objectives to align with the applicable CCMAS requirements.",
    ),
    "curriculum_aligned_with_BMAS": _rule(
        "Curriculum compliance", "academic_curriculum",
        "The curriculum does not adequately align with the applicable minimum academic standards.",
        "The institution should review and revise the curriculum to align fully with the applicable minimum academic standards and retain evidence of approval and implementation.",
    ),
    "innovative_courses_present": _rule(
        "Curriculum innovation", "academic_curriculum",
        "The curriculum does not provide adequate evidence of relevant innovation and contemporary course content.",
        "The institution should strengthen the curriculum with relevant contemporary and innovative course content and document its approval and delivery.",
    ),
    "curriculum_coverage_complete": _rule(
        "Curriculum coverage", "academic_curriculum",
        "The programme does not adequately cover the approved curriculum.",
        "The institution should ensure complete delivery of the approved curriculum and maintain course files that demonstrate the required coverage.",
    ),
    "admission_requirements_compliant": _rule(
        "Admission requirements", "academic_admission",
        "The programme's admission practices do not adequately comply with the prescribed entry requirements.",
        "The institution should enforce the prescribed admission requirements and retain complete records demonstrating compliance for every admitted student.",
    ),
    "academic_regulations_defined": _rule(
        "Academic regulations", "academic_governance",
        "Academic regulations are absent, incomplete or not being applied effectively.",
        "The institution should approve, communicate and consistently apply comprehensive academic regulations for the programme.",
    ),
    "tests_and_examinations_standardized": _rule(
        "Tests and examinations", "academic_assessment",
        "The standard and administration of tests and examinations are inadequate.",
        "The institution should strengthen test and examination setting, moderation, administration and record-keeping in accordance with the approved academic regulations.",
    ),
    "evaluation_methods_clear": _rule(
        "Evaluation of students' work", "academic_assessment",
        "The methods used to evaluate students' work are not sufficiently clear or consistently applied.",
        "The institution should define, communicate and consistently apply appropriate assessment methods and retain moderated assessment records.",
    ),
    "degree_projects_adequate": _rule(
        "Degree projects", "academic_projects",
        "Degree projects are inadequate in quality, relevance, originality or supervision.",
        "The institution should strengthen project topic selection, supervision, quality assurance and archiving to ensure relevant and original student work.",
    ),
    "practical_work_adequate": _rule(
        "Practical work", "academic_practical",
        "Practical work is insufficient in quality, depth or curriculum coverage.",
        "The institution should provide and document adequate practical activities covering the approved curriculum, with appropriate supervision and resources.",
    ),
    "student_course_evaluation_present": _rule(
        "Students' course evaluation", "academic_quality",
        "Student evaluation of courses and the learning environment is inadequate or ineffective.",
        "The institution should implement an effective course-evaluation process, analyse the feedback and document resulting improvements.",
    ),
    "skills_acquisition_programme": _rule(
        "Skills acquisition", "academic_skills",
        "Students do not demonstrate an adequate level of programme-relevant hard and soft skills.",
        "The institution should strengthen structured skills-acquisition activities and retain evidence of students' attainment of relevant hard and soft skills.",
    ),
    "external_examiner_system": _rule(
        "External examination", "academic_quality",
        "The external examination system is absent or not operating to an adequate standard.",
        "The institution should engage suitably qualified external examiners, act on their reports and retain evidence of the complete external examination process.",
    ),
    "internal_quality_assurance": _rule(
        "Internal quality assurance", "academic_quality",
        "The programme lacks an effective internal quality assurance system.",
        "The institution should establish or strengthen the programme's internal quality assurance system and document regular monitoring and corrective action.",
    ),
    # Staffing
    "staff_student_ratio_compliant": _rule(
        "Staff-student ratio", "staffing_capacity",
        "The number of academic staff is inadequate for the programme's student population.",
        "The institution should recruit sufficient qualified academic staff and manage enrolment to achieve the prescribed staff-student ratio.",
    ),
    "proportion_core_staff_sufficient": _rule(
        "Core academic staff", "staffing_capacity",
        "The programme has an inadequate proportion of academic staff core to the discipline.",
        "The institution should recruit and retain additional qualified academic staff whose expertise is core to the programme discipline.",
    ),
    "staff_rank_mix_balanced": _rule(
        "Academic staff rank mix", "staffing_profile",
        "The academic staff rank mix is not adequately balanced.",
        "The institution should recruit and develop academic staff to achieve the prescribed balance across professorial, senior and other academic ranks.",
    ),
    "academic_staff_qualification_high": _rule(
        "Academic staff qualifications", "staffing_qualification",
        "The proportion of appropriately qualified academic staff is inadequate.",
        "The institution should recruit appropriately qualified academic staff and support existing staff to obtain the required higher qualifications.",
    ),
    "staff_competence_verified": _rule(
        "Teaching staff competence", "staffing_qualification",
        "The competence of teaching staff is not adequately demonstrated.",
        "The institution should verify staff competence, address identified gaps through recruitment or development, and maintain supporting records.",
    ),
    "administrative_support_available": _rule(
        "Programme administration", "staffing_administration",
        "Programme administration is not sufficiently effective or appropriately led.",
        "The institution should assign appropriately qualified academic leadership and strengthen the programme's administrative processes and records.",
    ),
    "non_teaching_staff_adequate": _rule(
        "Non-teaching staff", "staffing_capacity",
        "The programme has inadequate non-teaching staff support.",
        "The institution should provide sufficient qualified technical and administrative staff to support programme delivery.",
    ),
    "academic_staff_development_programme": _rule(
        "Academic staff development", "staffing_development",
        "Academic staff development is inadequate.",
        "The institution should implement and document a sustained academic staff development programme addressing identified teaching and research needs.",
    ),
    "non_academic_staff_development_programme": _rule(
        "Non-academic staff development", "staffing_development",
        "Development opportunities for non-academic staff are inadequate.",
        "The institution should implement and document relevant development activities for technical and administrative staff.",
    ),
    # Physical Facilities
    "laboratory_space_adequate": _rule(
        "Laboratory and practical space", "facilities_practical",
        "Laboratory, clinic, studio or other practical space is inadequate for programme delivery.",
        "The institution should provide sufficient fit-for-purpose practical space that meets the applicable programme requirements.",
    ),
    "laboratory_equipment_adequate": _rule(
        "Laboratory equipment", "facilities_practical",
        "Laboratory or practical equipment is inadequate in quality, quantity or functionality.",
        "The institution should procure, maintain and make available sufficient functional equipment that meets the programme specifications.",
    ),
    "classroom_space_adequate": _rule(
        "Classroom space", "facilities_teaching",
        "Available classroom or lecture theatre space is inadequate for the programme.",
        "The institution should provide adequate classroom and lecture theatre capacity that meets the applicable space standards.",
    ),
    "classroom_equipment_adequate": _rule(
        "Classroom equipment", "facilities_teaching",
        "Classroom equipment is inadequate or poorly maintained.",
        "The institution should provide and maintain sufficient functional classroom equipment to support effective teaching and learning.",
    ),
    "office_accommodation_adequate": _rule(
        "Office accommodation", "facilities_office",
        "Office accommodation is inadequate in space or equipment.",
        "The institution should provide appropriately sized and equipped office accommodation for programme staff.",
    ),
    "safety_environment_present": _rule(
        "Safety and environment", "facilities_safety",
        "The programme environment does not adequately meet applicable safety, fire and sanitation requirements.",
        "The institution should correct the identified safety, fire and sanitation shortcomings and maintain evidence of regular compliance checks.",
    ),
    # Library
    "library_holdings_adequate": _rule(
        "Library holdings", "library_resources",
        "Relevant library holdings are inadequate in number, quality or coverage for the programme.",
        "The institution should procure sufficient high-quality and relevant textbooks, journals and other materials to provide adequate programme coverage.",
    ),
    "library_material_current": _rule(
        "Currency of holdings", "library_resources",
        "Recommended texts or journals are not sufficiently current for the programme.",
        "The institution should update recommended texts and journals and establish a documented process for keeping programme holdings current.",
    ),
    "e_library_subscription_available": _rule(
        "Electronic library subscriptions", "library_digital",
        "Electronic library subscriptions do not provide adequate access to relevant academic databases and materials.",
        "The institution should subscribe to relevant academic databases and maintain dependable access to current electronic books and journals.",
    ),
    "e_library_access_good": _rule(
        "Electronic library access", "library_digital",
        "Access channels for available electronic books and journals are inadequate.",
        "The institution should provide reliable and convenient campus access to available electronic library resources.",
    ),
    # Other assessed categories
    "programme_funding_adequate": _rule(
        "Programme funding", "funding",
        "Recorded annual programme funding falls within an inadequate assessment band.",
        "The institution should increase and reliably release programme funding to support its documented teaching, staffing, facilities, library and quality assurance needs.",
    ),
    "research_collaboration_active": _rule(
        "Research and collaboration", "research",
        "Research and collaboration activities are inadequate or insufficiently multidisciplinary and applied.",
        "The institution should strengthen documented research and collaboration activities, including relevant multidisciplinary participation and application of results.",
    ),
    "research_output_present": _rule(
        "Research output", "research",
        "Evidence of relevant research output is inadequate.",
        "The institution should support relevant research activity and maintain verifiable records of resulting outputs and impact.",
    ),
    "employer_rating_positive": _rule(
        "Graduate tracer and employer rating", "tracer",
        "A functional graduate tracer system or satisfactory evidence of graduates' workplace performance is lacking.",
        "The institution should establish or strengthen a graduate tracer system and maintain appropriate records of graduates' employment and workplace performance.",
    ),
    "tracer_study_available": _rule(
        "Graduate tracer study", "tracer",
        "Evidence of a functional graduate tracer study is inadequate.",
        "The institution should conduct regular graduate tracer studies, analyse the findings and document resulting programme improvements.",
    ),
}


CATEGORY_FALLBACKS: dict[str, tuple[str, str]] = {
    "Academic Matters": (
        "Recorded academic matters do not adequately satisfy the programme assessment requirements.",
        "The institution should review the underlying academic-matters responses, correct the documented weaknesses and retain evidence for reassessment.",
    ),
    "Staffing": (
        "Recorded staffing provision is inadequate for effective programme delivery.",
        "The institution should address the documented staffing gaps through appropriate recruitment, development and deployment of qualified personnel.",
    ),
    "Physical Facilities": (
        "Recorded physical facilities are inadequate for effective programme delivery.",
        "The institution should provide and maintain the facilities and equipment identified as inadequate in the assessment evidence.",
    ),
    "Library": (
        "Recorded library provision is inadequate for the programme's teaching, learning and research needs.",
        "The institution should strengthen the library resources and access arrangements identified as inadequate in the assessment evidence.",
    ),
    "Funding": (
        "Recorded programme funding is inadequate to support programme needs.",
        "The institution should provide and reliably release adequate programme funding against a documented improvement plan.",
    ),
    "Research and Collaboration": (
        "Recorded research and collaboration activity is inadequate.",
        "The institution should strengthen and document relevant research and collaboration activities and their outcomes.",
    ),
    "Tracer and Employers' Rating": (
        "Evidence of graduate tracing or employer assessment is inadequate.",
        "The institution should strengthen graduate tracing and maintain evidence of employer feedback and resulting programme improvements.",
    ),
}


def humanize_criterion(name: str) -> str:
    return name.replace("_", " ").strip().title()


def _finding(
    number: int,
    category: str,
    criterion: str,
    deficiency: str,
    remedy: str,
    source_ids: list[str],
    *,
    missing: bool = False,
) -> Finding:
    return Finding(
        id=f"D{number:03d}",
        category=category,
        criterion=criterion,
        deficiency=deficiency,
        remedy=remedy,
        source_criterion_ids=tuple(source_ids),
        observed_performance="No response recorded" if missing else "Recorded assessment response indicates a weakness",
        expected_standard="A verified assessment response" if missing else "A satisfactory response under the configured assessment rubric",
        priority="High" if category in CORE_CATEGORIES or missing else "Medium",
        timeframe="Before finalising the assessment" if missing else "As part of the programme improvement plan",
    )


def generate_findings(
    section_scores: Mapping[str, float | None],
    criterion_responses: Mapping[str, Mapping[str, float | None]],
) -> list[Finding]:
    """Return consolidated findings supported by recorded responses."""

    findings: list[Finding] = []
    for category in SECTION_MAX:
        responses = criterion_responses.get(category, {})
        grouped: dict[str, list[tuple[str, CriterionRule]]] = {}
        missing_ids: list[str] = []

        for criterion_id, value in responses.items():
            if value is None:
                missing_ids.append(criterion_id)
                continue
            rule = CRITERION_RULES.get(criterion_id)
            if rule is not None and float(value) < rule.minimum_normalized_score:
                grouped.setdefault(rule.group, []).append((criterion_id, rule))

        for items in grouped.values():
            source_ids = [criterion_id for criterion_id, _ in items]
            rules = [rule for _, rule in items]
            findings.append(_finding(
                len(findings) + 1,
                category,
                ", ".join(rule.label for rule in rules),
                " ".join(dict.fromkeys(rule.deficiency for rule in rules)),
                " ".join(dict.fromkeys(rule.remedy for rule in rules)),
                source_ids,
            ))

        if missing_ids:
            labels = [
                CRITERION_RULES[item].label if item in CRITERION_RULES else humanize_criterion(item)
                for item in missing_ids
            ]
            findings.append(_finding(
                len(findings) + 1,
                category,
                ", ".join(labels),
                f"Required assessment information is missing for {', '.join(labels)}; compliance cannot be determined.",
                f"The institution should provide and verify the missing information for {', '.join(labels)} before finalising the assessment.",
                missing_ids,
                missing=True,
            ))

        value = section_scores.get(category)
        has_detailed_finding = bool(grouped or missing_ids)
        if value is None and not responses:
            findings.append(_finding(
                len(findings) + 1,
                category,
                "Assessment information",
                f"Required assessment information for {category} is missing; compliance cannot be determined.",
                f"The institution should complete and verify all required {category.lower()} responses before finalising the assessment.",
                [],
                missing=True,
            ))
        elif value is not None and not has_detailed_finding:
            percentage = score_percentage(float(value), SECTION_MAX[category])
            if percentage < 70:
                deficiency, remedy = CATEGORY_FALLBACKS[category]
                findings.append(_finding(
                    len(findings) + 1,
                    category,
                    f"{category} assessment evidence",
                    deficiency,
                    remedy,
                    list(responses),
                ))

    evidence_responses = criterion_responses.get("Assessment Evidence", {})
    missing_evidence = [key for key, value in evidence_responses.items() if value is None]
    if missing_evidence:
        findings.append(_finding(
            len(findings) + 1,
            "Assessment Evidence",
            ", ".join(humanize_criterion(item) for item in missing_evidence),
            "Required assessment information is missing or unresolved, so compliance cannot be determined.",
            "The institution should provide and verify the missing or conflicting assessment information before finalising the assessment.",
            missing_evidence,
            missing=True,
        ))

    return findings


def build_report_data(
    *,
    institution: str,
    discipline: str,
    programme: str,
    accreditation_status: str,
    findings: list[Finding],
    assessment_date: date | str | None = None,
) -> dict[str, Any]:
    if assessment_date is None:
        display_date = date.today().strftime("%d %B %Y")
    elif isinstance(assessment_date, date):
        display_date = assessment_date.strftime("%d %B %Y")
    else:
        try:
            display_date = date.fromisoformat(str(assessment_date)[:10]).strftime("%d %B %Y")
        except ValueError:
            display_date = str(assessment_date)

    status = accreditation_status.removesuffix(" ACCREDITATION").strip().upper()
    return {
        "accreditation_status": f"{status} ACCREDITATION",
        "summary": {
            "assessment_date": display_date,
            "institution": institution,
            "discipline": discipline,
            "programme": programme,
            "status": f"{status} ACCREDITATION",
        },
        "findings": [finding.to_dict() for finding in findings],
    }


def format_markdown_report(report: Mapping[str, Any]) -> str:
    """Render the exact four-section public report."""

    summary = report["summary"]
    findings = report["findings"]
    if findings:
        deficiency_text = "\n".join(
            f"{index}. {item['deficiency']}" for index, item in enumerate(findings, start=1)
        )
        remedy_text = "\n".join(
            f"{index}. {item['remedy']}" for index, item in enumerate(findings, start=1)
        )
    else:
        deficiency_text = "No substantiated deficiencies were identified from the completed assessment responses."
        remedy_text = "Maintain the documented programme controls and supporting evidence for future review."

    return f"""## Accreditation Status

**{report['accreditation_status']}**

## Accreditation Assessment Summary

- **Assessment date:** {summary['assessment_date']}
- **Institution name:** {summary['institution']}
- **Discipline:** {summary['discipline']}
- **Programme name:** {summary['programme']}
- **Accreditation status:** {summary['status']}

## Deficiencies

{deficiency_text}

## Remedies

{remedy_text}"""


def build_deterministic_report(
    *,
    institution: str,
    discipline: str,
    programme: str,
    accreditation_status: str,
    findings: list[Finding],
    assessment_date: date | str | None = None,
    programme_score: float | None = None,
    section_scores: Mapping[str, float] | None = None,
) -> str:
    """Build the public report; score arguments remain for caller compatibility."""

    del programme_score, section_scores
    return format_markdown_report(build_report_data(
        institution=institution,
        discipline=discipline,
        programme=programme,
        accreditation_status=accreditation_status,
        findings=findings,
        assessment_date=assessment_date,
    ))


def findings_as_records(findings: list[Finding]) -> list[dict[str, Any]]:
    return [finding.to_dict() for finding in findings]
