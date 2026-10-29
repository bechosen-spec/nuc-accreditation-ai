"""Deterministic deficiencies and remedies reporting.

Reports generated here never require an external AI service.  Findings are
derived only from submitted criterion values and calculated section scores.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from assessment_rules import CORE_CATEGORIES, SECTION_MAX, score_percentage


@dataclass(frozen=True)
class Finding:
    category: str
    criterion: str
    observed_performance: str
    expected_standard: str
    deficiency: str
    recommended_action: str
    priority: str
    timeframe: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def humanize_criterion(name: str) -> str:
    return name.replace("_", " ").strip().title()


def generate_findings(
    section_scores: dict[str, float],
    criterion_responses: dict[str, dict[str, float | None]],
) -> list[Finding]:
    """Generate evidence-bounded findings from calculated assessment data."""

    findings: list[Finding] = []
    for category in CORE_CATEGORIES:
        value = section_scores.get(category)
        if value is None:
            findings.append(Finding(
                category=category,
                criterion="Core category score",
                observed_performance="Not calculated",
                expected_standard="A complete, validated category score",
                deficiency="Information is insufficient to assess this core category.",
                recommended_action="Complete and validate all required responses for this category, then rerun the assessment.",
                priority="Critical",
                timeframe="Immediate",
            ))
            continue

        percentage = score_percentage(value, SECTION_MAX[category])
        if percentage < 70:
            denied = percentage < 60
            findings.append(Finding(
                category=category,
                criterion="Core category performance",
                observed_performance=f"{percentage:.2f}%",
                expected_standard="At least 70.00% for full accreditation",
                deficiency=(
                    "Core category is below the 60% minimum and triggers denied accreditation."
                    if denied
                    else "Core category is below the 70% full-accreditation threshold."
                ),
                recommended_action=f"Address the lowest-scoring recorded criteria in {category} and reassess with supporting evidence.",
                priority="Critical" if denied else "High",
                timeframe="Immediate to 3 months" if denied else "Within 3 months",
            ))

    for category, responses in criterion_responses.items():
        for criterion, normalized_score in responses.items():
            criterion_name = humanize_criterion(criterion)
            if normalized_score is None:
                findings.append(Finding(
                    category=category,
                    criterion=criterion_name,
                    observed_performance="No response recorded",
                    expected_standard="A verified assessment response",
                    deficiency="Required assessment information is missing; compliance cannot be determined.",
                    recommended_action="Provide and verify the missing response and its supporting evidence.",
                    priority="High" if category in CORE_CATEGORIES else "Medium",
                    timeframe="Before finalising the assessment",
                ))
            elif normalized_score < 0.7:
                findings.append(Finding(
                    category=category,
                    criterion=criterion_name,
                    observed_performance=f"{normalized_score * 100:.2f}% of the configured criterion score",
                    expected_standard="At least 70.00% of the configured criterion score",
                    deficiency="The recorded response indicates a performance gap for this criterion.",
                    recommended_action=f"Review {criterion_name.lower()}, implement a documented corrective action, and retain evidence for reassessment.",
                    priority="High" if normalized_score < 0.6 and category in CORE_CATEGORIES else "Medium",
                    timeframe="Within 3 months" if category in CORE_CATEGORIES else "Within 6 months",
                ))

    return findings


def build_deterministic_report(
    *,
    institution: str,
    discipline: str,
    programme: str,
    programme_score: float,
    accreditation_status: str,
    section_scores: dict[str, float],
    findings: list[Finding],
) -> str:
    """Build a repeatable Markdown report from the assessment calculation."""

    section_lines = "\n".join(
        f"- **{name}:** {score_percentage(section_scores[name], maximum):.2f}%"
        for name, maximum in SECTION_MAX.items()
        if name in section_scores and section_scores[name] is not None
    )

    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.category].append(finding)

    if grouped:
        finding_sections = []
        counter = 1
        for category, items in grouped.items():
            finding_sections.append(f"### {category}")
            for item in items:
                finding_sections.append(
                    f"{counter}. **Criterion:** {item.criterion}  \n"
                    f"   **Current observed performance:** {item.observed_performance}  \n"
                    f"   **Expected standard or threshold:** {item.expected_standard}  \n"
                    f"   **Identified deficiency:** {item.deficiency}  \n"
                    f"   **Recommended corrective action:** {item.recommended_action}  \n"
                    f"   **Priority:** {item.priority}  \n"
                    f"   **Suggested timeframe:** {item.timeframe}"
                )
                counter += 1
        findings_text = "\n\n".join(finding_sections)
    else:
        findings_text = (
            "No deficiencies were identified from the completed assessment responses. "
            "Maintain current controls and supporting evidence."
        )

    return f"""
## Accreditation Assessment Summary

- **Assessment date:** {date.today().strftime('%d %B %Y')}
- **Institution:** {institution}
- **Discipline:** {discipline}
- **Programme:** {programme}
- **Accreditation status:** {accreditation_status} ACCREDITATION
- **Programme score:** {programme_score:.2f}%

## Core Accreditation Performance

{section_lines}

## Deficiencies and Recommended Remedies

{findings_text}

## Advisory Disclaimer

This report is a deterministic accreditation-readiness assessment based only on the recorded responses and calculated rules. It does not issue an official NUC accreditation decision.
""".strip()


def findings_as_records(findings: list[Finding]) -> list[dict[str, Any]]:
    return [finding.to_dict() for finding in findings]
