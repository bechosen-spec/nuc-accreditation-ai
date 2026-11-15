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
        "academic_philosophy",
        "The programme philosophy and objectives do not meet the applicable CCMAS statement-and-alignment criterion.",
        "The institution should revise and formally document the programme philosophy and objectives to align with the applicable CCMAS requirements.",
    ),
    "curriculum_aligned_with_BMAS": _rule(
        "Curriculum compliance", "academic_curriculum",
        "The curriculum does not adequately align with the applicable minimum academic standards.",
        "The institution should review and revise the curriculum to align fully with the applicable minimum academic standards and retain evidence of approval and implementation.",
    ),
    "innovative_courses_present": _rule(
        "Curriculum innovation", "academic_innovation",
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
        "Academic regulations", "academic_regulations",
        "Academic regulations do not meet the required standard for availability, clarity, use and communication to students.",
        "The institution should approve, communicate and consistently apply comprehensive academic regulations for the programme.",
    ),
    "tests_and_examinations_standardized": _rule(
        "Tests and examinations", "academic_tests",
        "The standard and administration of tests and examinations are inadequate.",
        "The institution should strengthen test and examination setting, moderation, administration and record-keeping in accordance with the approved academic regulations.",
    ),
    "evaluation_methods_clear": _rule(
        "Evaluation of students' work", "academic_evaluation",
        "Evaluation of students' work does not meet the required marking-scheme and grading-consistency standard.",
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
        "Students' course evaluation", "academic_course_evaluation",
        "Student evaluation of courses and the learning environment does not meet the required adequacy standard.",
        "The institution should implement an effective course-evaluation process, analyse the feedback and document resulting improvements.",
    ),
    "skills_acquisition_programme": _rule(
        "Skills acquisition", "academic_skills",
        "Students do not demonstrate an adequate level of programme-relevant hard and soft skills.",
        "The institution should strengthen structured skills-acquisition activities and retain evidence of students' attainment of relevant hard and soft skills.",
    ),
    "external_examiner_system": _rule(
        "External examination", "academic_external_examination",
        "The external examination system does not meet the required assessor-qualification and work-quality standard.",
        "The institution should engage suitably qualified external examiners, act on their reports and retain evidence of the complete external examination process.",
    ),
    "internal_quality_assurance": _rule(
        "Internal quality assurance", "academic_internal_quality",
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
        "Core academic staff", "staffing_core",
        "The programme has an inadequate proportion of academic staff core to the discipline.",
        "The institution should recruit and retain additional qualified academic staff whose expertise is core to the programme discipline.",
    ),
    "staff_rank_mix_balanced": _rule(
        "Academic staff rank mix", "staffing_rank_mix",
        "The academic staff rank mix is not adequately balanced.",
        "The institution should recruit and develop academic staff to achieve the prescribed balance across professorial, senior and other academic ranks.",
    ),
    "academic_staff_qualification_high": _rule(
        "Academic staff qualifications", "staffing_academic_qualification",
        "The proportion of appropriately qualified academic staff is inadequate.",
        "The institution should recruit appropriately qualified academic staff and support existing staff to obtain the required higher qualifications.",
    ),
    "staff_competence_verified": _rule(
        "Teaching staff competence", "staffing_competence",
        "The competence of teaching staff is not adequately demonstrated.",
        "The institution should verify staff competence, address identified gaps through recruitment or development, and maintain supporting records.",
    ),
    "administrative_support_available": _rule(
        "Programme administration", "staffing_administration",
        "Programme administration does not meet the required leadership and effectiveness standard.",
        "The institution should assign appropriately qualified academic leadership and strengthen the programme's administrative processes and records.",
    ),
    "non_teaching_staff_adequate": _rule(
        "Non-teaching staff", "staffing_non_teaching",
        "The programme has inadequate non-teaching staff support.",
        "The institution should provide sufficient qualified technical and administrative staff to support programme delivery.",
    ),
    "academic_staff_development_programme": _rule(
        "Academic staff development", "staffing_academic_development",
        "Academic staff development is inadequate.",
        "The institution should implement and document a sustained academic staff development programme addressing identified teaching and research needs.",
    ),
    "non_academic_staff_development_programme": _rule(
        "Non-academic staff development", "staffing_non_academic_development",
        "Development opportunities for non-academic staff are inadequate.",
        "The institution should implement and document relevant development activities for technical and administrative staff.",
    ),
    # Physical Facilities
    "laboratory_space_adequate": _rule(
        "Laboratory and practical space", "facilities_practical_space",
        "Laboratory or other practical space does not meet the required programme space standard.",
        "The institution should provide sufficient fit-for-purpose practical space that meets the applicable programme requirements.",
    ),
    "laboratory_equipment_adequate": _rule(
        "Laboratory equipment", "facilities_practical_equipment",
        "Laboratory equipment does not meet the required CCMAS specification compliance level.",
        "The institution should procure, maintain and make available sufficient functional equipment that meets the programme specifications.",
    ),
    "classroom_space_adequate": _rule(
        "Classroom space", "facilities_classroom_space",
        "Available classroom or lecture theatre space is inadequate for the programme.",
        "The institution should provide adequate classroom and lecture theatre capacity that meets the applicable space standards.",
    ),
    "classroom_equipment_adequate": _rule(
        "Classroom equipment", "facilities_classroom_equipment",
        "Classroom equipment does not meet the combined adequacy and maintenance criterion.",
        "The institution should provide and maintain sufficient functional classroom equipment to support effective teaching and learning.",
    ),
    "office_accommodation_adequate": _rule(
        "Office accommodation", "facilities_office",
        "Office accommodation does not meet the assessed space-and-equipment standard.",
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
        "Research and collaboration", "research_collaboration",
        "Research and collaboration activity does not meet the assessed availability, multidisciplinary-engagement and application standard.",
        "The institution should strengthen documented research and collaboration activities, including relevant multidisciplinary participation and application of results.",
    ),
    "research_output_present": _rule(
        "Research output", "research_output",
        "Evidence of relevant research output is inadequate.",
        "The institution should support relevant research activity and maintain verifiable records of resulting outputs and impact.",
    ),
    "employer_rating_positive": _rule(
        "Graduate tracer and employer rating", "tracer",
        "Graduate tracing and employer-rating evidence does not meet the assessed standard.",
        "The institution should establish or strengthen a graduate tracer system and maintain appropriate records of graduates' employment and workplace performance.",
    ),
    "supervised_industrial_experience": _rule(
        "Supervised industrial experience", "industrial_experience",
        "Students' performance during supervised industrial and similar experience does not meet the required standard.",
        "The institution should review supervised industrial placements, supervision and learning support, then document improvement in students' performance.",
    ),
    "tracer_study_available": _rule(
        "Graduate tracer study", "tracer",
        "Evidence of a functional graduate tracer study is inadequate.",
        "The institution should conduct regular graduate tracer studies, analyse the findings and document resulting programme improvements.",
    ),
}


# Response-specific wording is used where a rubric option establishes a
# narrower fact than the criterion-level fallback. Keys are normalized scores
# stored by the manual questionnaire.
RESPONSE_SPECIFIC_FINDINGS: dict[str, dict[float, tuple[str, str]]] = {
    "degree_projects_adequate": {
        0.5: (
            "Degree projects are innovative and creative but are not adequately supervised.",
            "The institution should strengthen project-supervisor allocation, monitoring and documented feedback.",
        ),
        0.0: (
            "Degree projects are not adequately supervised and do not demonstrate the required creativity and innovation.",
            "The institution should improve project supervision and require project selection and assessment processes that demonstrate creativity and innovation.",
        ),
    },
    "practical_work_adequate": {
        0.66: (
            "Practical work is conducted to a good standard but does not adequately cover the approved curriculum.",
            "The institution should extend the practical-work schedule to cover the approved curriculum and retain evidence of delivery.",
        ),
        0.33: (
            "Practical work is conducted but does not meet the required quality standard.",
            "The institution should improve the design, delivery and quality assurance of practical work and retain evidence of the improved standard.",
        ),
        0.0: (
            "Required practical work is not conducted.",
            "The institution should implement and document the practical work required by the approved curriculum.",
        ),
    },
    "laboratory_space_adequate": {
        0.66: (
            "Available practical space meets only 60% but less than 70% of the NUC space standard.",
            "The institution should expand or reconfigure practical space to meet at least 70% of the applicable NUC space standard.",
        ),
        0.33: (
            "Available practical space meets only 50% but less than 60% of the NUC space standard.",
            "The institution should expand or reconfigure practical space to meet at least 70% of the applicable NUC space standard.",
        ),
        0.0: (
            "Available practical space meets less than 50% of the NUC space standard.",
            "The institution should provide sufficient fit-for-purpose practical space to meet at least 70% of the applicable NUC space standard.",
        ),
    },
    "laboratory_equipment_adequate": {
        0.5: (
            "Laboratory equipment meets only 60% but less than 70% of the CCMAS specification.",
            "The institution should close the documented equipment gap so compliance reaches the required CCMAS level.",
        ),
        0.25: (
            "Laboratory equipment meets only 50% but less than 60% of the CCMAS specification.",
            "The institution should procure and commission the equipment needed to reach the required CCMAS compliance level.",
        ),
        0.0: (
            "Laboratory equipment meets less than 50% of the CCMAS specification.",
            "The institution should implement a documented procurement and commissioning plan to reach the required CCMAS compliance level.",
        ),
    },
    "classroom_equipment_adequate": {
        0.5: (
            "Classroom equipment only partially meets the combined adequacy and maintenance criterion.",
            "The institution should verify the recorded classroom-equipment gap and correct the affected criterion.",
        ),
        0.0: (
            "Classroom equipment is inadequate and not well maintained.",
            "The institution should provide adequate classroom equipment and implement a documented maintenance programme.",
        ),
    },
    "office_accommodation_adequate": {
        0.66: (
            "Office accommodation is well equipped but slightly inadequate in space.",
            "The institution should increase office space for programme staff while maintaining the existing equipment provision.",
        ),
        0.33: (
            "Office accommodation only partially meets the combined space-and-equipment standard.",
            "The institution should verify and correct the recorded office-accommodation gap.",
        ),
        0.0: (
            "Office accommodation does not meet the required suitability standard.",
            "The institution should provide suitable office accommodation that meets the required space and equipment standard.",
        ),
    },
    "programme_funding_adequate": {
        1 / 3: (
            "Recorded annual programme funding is below ₦300,000.",
            "The institution should increase and reliably release annual programme funding to at least the adequate assessment band and document its use against programme needs.",
        ),
        2 / 3: (
            "Recorded annual programme funding is between ₦300,000 and below ₦1,000,000, which remains below the adequate assessment band.",
            "The institution should increase and reliably release annual programme funding to at least ₦1,000,000 and document its use against programme needs.",
        ),
    },
    "research_collaboration_active": {
        0.66: (
            "Research and collaboration are available and applied, but multidisciplinary engagement is not demonstrated.",
            "The institution should add and document relevant multidisciplinary participation in research and collaboration activities.",
        ),
        0.33: (
            "Research and collaboration are available, but multidisciplinary engagement and application of results are not demonstrated.",
            "The institution should document multidisciplinary participation and the application of results from research and collaboration activities.",
        ),
        0.0: (
            "Research and collaboration activity is not available.",
            "The institution should establish and document relevant research and collaboration activities.",
        ),
    },
    "employer_rating_positive": {
        0.5: (
            "Graduate tracing and workplace-performance evidence only partially meet the combined assessment criterion.",
            "The institution should identify and correct the unmet tracer-system or workplace-performance evidence requirement.",
        ),
        0.0: (
            "A graduate tracer system is not in place and recorded workplace performance is below average.",
            "The institution should establish a graduate tracer system and implement a documented plan to improve and monitor graduates' workplace performance.",
        ),
    },
    "supervised_industrial_experience": {
        0.5: (
            "Students' performance during supervised industrial and similar experience is rated Average.",
            "The institution should strengthen placement preparation, supervision and feedback to improve industrial-experience performance above Average.",
        ),
        0.0: (
            "Students' performance during supervised industrial and similar experience is rated Below average.",
            "The institution should review placements, supervision and learning support, then implement and document corrective action for below-average performance.",
        ),
    },
}


def criterion_rule_for_response(
    criterion_id: str,
    value: float,
) -> CriterionRule | None:
    """Return deterministic wording grounded in the selected rubric response."""

    base_rule = CRITERION_RULES.get(criterion_id)
    if base_rule is None:
        return None
    for expected, (deficiency, remedy) in RESPONSE_SPECIFIC_FINDINGS.get(criterion_id, {}).items():
        if abs(float(value) - expected) < 1e-9:
            return CriterionRule(
                label=base_rule.label,
                group=base_rule.group,
                deficiency=deficiency,
                remedy=remedy,
                minimum_normalized_score=base_rule.minimum_normalized_score,
            )
    return base_rule


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
    observed_performance: str | None = None,
) -> Finding:
    return Finding(
        id=f"D{number:03d}",
        category=category,
        criterion=criterion,
        deficiency=deficiency,
        remedy=remedy,
        source_criterion_ids=tuple(source_ids),
        observed_performance=(
            observed_performance
            or ("No response recorded" if missing else "Recorded assessment response indicates a weakness")
        ),
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
        grouped: dict[str, list[tuple[str, CriterionRule, float]]] = {}
        missing_ids: list[str] = []

        for criterion_id, value in responses.items():
            if value is None:
                missing_ids.append(criterion_id)
                continue
            rule = criterion_rule_for_response(criterion_id, float(value))
            if rule is not None and float(value) < rule.minimum_normalized_score:
                grouped.setdefault(rule.group, []).append((criterion_id, rule, float(value)))

        for group, items in grouped.items():
            source_ids = [criterion_id for criterion_id, _, _ in items]
            rules = [rule for _, rule, _ in items]
            deficiency = " ".join(dict.fromkeys(rule.deficiency for rule in rules))
            remedy = " ".join(dict.fromkeys(rule.remedy for rule in rules))
            if group == "academic_curriculum" and {
                "curriculum_aligned_with_BMAS",
                "curriculum_coverage_complete",
            }.issubset(source_ids):
                deficiency = (
                    "The curriculum does not adequately align with the applicable minimum "
                    "academic standards, including the required curriculum coverage."
                )
                remedy = (
                    "The institution should revise and implement the curriculum so it aligns "
                    "fully with the applicable minimum academic standards and required coverage."
                )
            findings.append(_finding(
                len(findings) + 1,
                category,
                ", ".join(rule.label for rule in rules),
                deficiency,
                remedy,
                source_ids,
                observed_performance="; ".join(
                    f"{criterion_id}={value:.2f} normalized"
                    for criterion_id, _, value in items
                ),
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
    tracer_applicability_note: str | None = None,
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
            "tracer_applicability_note": tracer_applicability_note,
        },
        "findings": [finding.to_dict() for finding in findings],
    }


def format_markdown_report(report: Mapping[str, Any]) -> str:
    """Render the exact four-section public report."""

    summary = report["summary"]
    findings = report["findings"]
    tracer_note = summary.get("tracer_applicability_note")
    tracer_summary = (
        f"\n- **Graduate tracer assessment:** {tracer_note}"
        if tracer_note
        else ""
    )
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
- **Accreditation status:** {summary['status']}{tracer_summary}

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
    tracer_applicability_note: str | None = None,
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
        tracer_applicability_note=tracer_applicability_note,
    ))


def findings_as_records(findings: list[Finding]) -> list[dict[str, Any]]:
    return [finding.to_dict() for finding in findings]
