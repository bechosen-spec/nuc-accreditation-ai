import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher

from config.institutions import INSTITUTION_ALIASES


CONFIRMED_THRESHOLD = 0.85
NEEDS_REVIEW_THRESHOLD = 0.60
FUZZY_ACCEPTANCE_RATIO = 0.88

INSTITUTION_LABEL_RE = re.compile(
    r"^\s*(?:name\s+of\s+institution|name\s+of\s+university|institution|university)\b\s*[:\-–]\s*(.+)",
    flags=re.IGNORECASE,
)

INSTITUTION_NAME_RE = re.compile(
    r"\b(?:University|Polytechnic|College)\s+(?:of\s+)?(?:[A-Z][A-Za-z&.'\-]+(?:,?\s+|$)){1,8}",
    flags=re.IGNORECASE,
)

STOP_AFTER_RE = re.compile(
    r"\b(?:faculty|department|programme|program|self[- ]study|accreditation|ccmas|date|address|phone|email)\b",
    flags=re.IGNORECASE,
)


@dataclass
class InstitutionCandidate:
    raw_candidate: str
    normalised_candidate: str
    matched_known_institution: str
    confidence: float
    source_file: str
    source_page_or_section: str
    evidence_text: str
    extraction_method: str
    status: str = "needs_review"


@dataclass
class InstitutionExtractionResult:
    raw_candidate: str
    normalised_candidate: str
    matched_known_institution: str
    confidence: float
    source_file: str
    source_page_or_section: str
    evidence_text: str
    status: str
    extraction_method: str
    alternative_candidates: list

    def to_field_evidence(self, user_confirmed=False):
        return {
            "field_name": "institution_name",
            "extracted_value": self.matched_known_institution or self.normalised_candidate,
            "confidence": self.confidence,
            "source_file": self.source_file,
            "source_page_or_section": self.source_page_or_section,
            "evidence_text": self.evidence_text,
            "status": self.status,
            "user_confirmed": user_confirmed,
            "extraction_method": self.extraction_method,
        }


def compact_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalise_institution_name(value):
    cleaned = compact_text(value)
    cleaned = re.sub(
        r"^(?:name\s+of\s+institution|name\s+of\s+university|institution|university)\s*[:\-–]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    cleaned = re.sub(r",{2,}", ",", cleaned)
    cleaned = re.sub(r"\s+([,:;])", r"\1", cleaned)
    cleaned = STOP_AFTER_RE.split(cleaned)[0].strip(" .,:;-\t")
    return compact_text(cleaned).strip("| ")


def match_known_institution(candidate, known_institutions, supporting_text=""):
    if not candidate:
        return "", 0.0, "none"

    candidate_norm = normalise_for_match(candidate)
    aliases = {alias.upper(): target for alias, target in INSTITUTION_ALIASES.items()}
    if candidate.strip().upper() in aliases:
        target = aliases[candidate.strip().upper()]
        confidence = 0.90 if normalise_for_match(target) in normalise_for_match(supporting_text) else 0.74
        return target, confidence, "alias_match"

    for institution in known_institutions:
        if candidate_norm == normalise_for_match(institution):
            return institution, 1.0, "exact_known_match"

    best_name = ""
    best_ratio = 0.0
    for institution in known_institutions:
        ratio = SequenceMatcher(None, candidate_norm, normalise_for_match(institution)).ratio()
        if ratio > best_ratio:
            best_name = institution
            best_ratio = ratio

    if best_ratio >= FUZZY_ACCEPTANCE_RATIO:
        return best_name, best_ratio, "fuzzy_known_match"
    return "", best_ratio, "unmatched_candidate"


def normalise_for_match(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def candidate_status(confidence):
    if confidence >= CONFIRMED_THRESHOLD:
        return "confirmed"
    if confidence >= NEEDS_REVIEW_THRESHOLD:
        return "needs_review"
    return "missing"


def iter_document_contexts(parsed_documents):
    for doc in parsed_documents:
        file_name = doc.get("file_name", "")
        for block in doc.get("text_blocks", []):
            yield file_name, block.get("section", ""), block.get("text", ""), "text"
        for table_index, table in enumerate(doc.get("tables", []), start=1):
            for row_index, row in enumerate(table, start=1):
                cells = [compact_text(cell) for cell in row]
                row_text = " | ".join(cell for cell in cells if cell)
                if row_text:
                    yield file_name, f"Table {table_index}, row {row_index}", row_text, "table"
                for cell_index, cell in enumerate(cells, start=1):
                    if cell:
                        yield file_name, f"Table {table_index}, cell {row_index}:{cell_index}", cell, "table_cell"


def extract_labeled_candidates(file_name, section, text, context_type, known_institutions):
    candidates = []
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    for line in lines:
        match = INSTITUTION_LABEL_RE.search(line)
        if not match:
            continue
        raw_value = normalise_institution_name(match.group(1))
        if not raw_value or (len(raw_value) < 3 and raw_value.upper() not in INSTITUTION_ALIASES):
            continue
        matched, match_score, match_method = match_known_institution(raw_value, known_institutions, text)
        confidence = max(0.72, min(0.98, match_score if matched else 0.68))
        if match_method == "alias_match":
            confidence = match_score
        candidates.append(InstitutionCandidate(
            raw_candidate=raw_value,
            normalised_candidate=normalise_institution_name(raw_value),
            matched_known_institution=matched,
            confidence=confidence,
            source_file=file_name,
            source_page_or_section=section,
            evidence_text=line[:300],
            extraction_method="label_and_heading_match" if context_type != "table_cell" else "table_label_match",
            status=candidate_status(confidence),
        ))
    return candidates


def extract_table_pair_candidates(file_name, section, text, known_institutions):
    if "|" not in text:
        return []
    cells = [normalise_institution_name(cell) for cell in text.split("|")]
    candidates = []
    for idx, cell in enumerate(cells[:-1]):
        if re.fullmatch(r"(?:name\s+of\s+institution|name\s+of\s+university|institution|university)", cell, flags=re.IGNORECASE):
            raw_value = cells[idx + 1]
            matched, match_score, match_method = match_known_institution(raw_value, known_institutions, text)
            confidence = max(0.74, min(0.98, match_score if matched else 0.70))
            if match_method == "alias_match":
                confidence = match_score
            candidates.append(InstitutionCandidate(
                raw_candidate=raw_value,
                normalised_candidate=normalise_institution_name(raw_value),
                matched_known_institution=matched,
                confidence=confidence,
                source_file=file_name,
                source_page_or_section=section,
                evidence_text=text[:300],
                extraction_method="table_label_match",
                status=candidate_status(confidence),
            ))
    return candidates


def extract_heading_candidates(file_name, section, text, known_institutions):
    candidates = []
    lines = [compact_text(line) for line in str(text).splitlines() if compact_text(line)]
    likely_heading_sections = bool(re.search(r"title|cover|header|footer|page 1|document body|sheet", section, flags=re.IGNORECASE))
    for line in lines[:40]:
        raw_value = ""
        if line.isupper() and ("UNIVERSITY" in line or "POLYTECHNIC" in line or "COLLEGE" in line):
            raw_value = line.title()
        else:
            match = INSTITUTION_NAME_RE.search(line)
            if match:
                raw_value = match.group(0)
        raw_value = normalise_institution_name(raw_value)
        if not raw_value:
            continue
        matched, match_score, match_method = match_known_institution(raw_value, known_institutions, text)
        base = 0.80 if likely_heading_sections else 0.68
        confidence = min(0.96, max(base, match_score if matched else base))
        if match_method == "alias_match":
            confidence = match_score
        candidates.append(InstitutionCandidate(
            raw_candidate=raw_value,
            normalised_candidate=raw_value,
            matched_known_institution=matched,
            confidence=confidence,
            source_file=file_name,
            source_page_or_section=section,
            evidence_text=line[:300],
            extraction_method="label_and_heading_match",
            status=candidate_status(confidence),
        ))
    return candidates


def collect_institution_candidates(parsed_documents, known_institutions):
    candidates = []
    for file_name, section, text, context_type in iter_document_contexts(parsed_documents):
        candidates.extend(extract_labeled_candidates(file_name, section, text, context_type, known_institutions))
        candidates.extend(extract_table_pair_candidates(file_name, section, text, known_institutions))
        candidates.extend(extract_heading_candidates(file_name, section, text, known_institutions))
    return dedupe_candidates(candidates)


def dedupe_candidates(candidates):
    best_by_name = {}
    for candidate in candidates:
        identity = normalise_for_match(candidate.matched_known_institution or candidate.normalised_candidate)
        if not identity:
            continue
        if identity not in best_by_name or candidate.confidence > best_by_name[identity].confidence:
            best_by_name[identity] = candidate
    return sorted(best_by_name.values(), key=lambda item: item.confidence, reverse=True)


def extract_institution_name(parsed_documents, known_institutions):
    candidates = collect_institution_candidates(parsed_documents, known_institutions)
    if not candidates:
        return InstitutionExtractionResult("", "", "", 0.0, "", "", "", "missing", "none", [])

    credible = [candidate for candidate in candidates if candidate.confidence >= NEEDS_REVIEW_THRESHOLD]
    identities = {
        normalise_for_match(candidate.matched_known_institution or candidate.normalised_candidate)
        for candidate in credible
    }
    if len(identities) > 1:
        best = candidates[0]
        return InstitutionExtractionResult(
            best.raw_candidate,
            best.normalised_candidate,
            best.matched_known_institution,
            min(best.confidence, 0.59),
            best.source_file,
            best.source_page_or_section,
            best.evidence_text,
            "conflicting",
            best.extraction_method,
            [asdict(candidate) for candidate in candidates],
        )

    best = candidates[0]
    return InstitutionExtractionResult(
        best.raw_candidate,
        best.normalised_candidate,
        best.matched_known_institution,
        best.confidence,
        best.source_file,
        best.source_page_or_section,
        best.evidence_text,
        best.status,
        best.extraction_method,
        [asdict(candidate) for candidate in candidates[1:]],
    )


def institution_is_resolved(confirmed_value):
    return bool(compact_text(confirmed_value))
