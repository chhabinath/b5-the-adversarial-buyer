"""Normalize and group related raw evidence without losing source records."""

from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from app.models.evidence import Evidence


@dataclass(frozen=True)
class EvidenceGroupCandidate:
    section: str
    feature: str
    limit: str | None
    pricing: str | None
    evidence: list[Evidence]


def _normalized_section(row: Evidence, feature: str) -> str:
    haystack = f"{row.section} {row.text}".lower()
    page_url = row.page.url if row.page is not None else ""
    is_vercel = (urlsplit(page_url).hostname or "").lower().endswith("vercel.com")
    if "firewall" in haystack:
        return "Vercel Firewall" if is_vercel else "Firewall"
    if any(term in haystack for term in ("active cpu", "fluid compute", "vercel functions")):
        return "Vercel Compute" if is_vercel else "Compute"
    return row.section.strip() or "Page"


def _feature_name(row: Evidence) -> str | None:
    haystack = row.text.lower()
    if "firewall rate limit requests" in haystack:
        return "Firewall Rate Limit Requests"
    if "active cpu" in haystack:
        return "Fluid Active CPU"
    match = re.search(r"(?:support|feature)\s*:?[ ]+([A-Z][\w -]{3,60})", row.text)
    return match.group(1).strip() if match else None


def _value_snippet(text: str, value_type: str) -> str:
    if value_type == "limit":
        match = re.search(r"(?i)(\d[\w/. -]*(?:included|limit(?:s)?))", text)
    else:
        match = re.search(
            r"(?i)((?:starting at|starts at|from)\s+\$\d+(?:\.\d+)?(?:\s+(?:per|/)\s+[^.;]+)?|\$\d+(?:\.\d+)?(?:\s+(?:per|/)\s+[^.;]+)?)",
            text,
        )
    return match.group(1).strip() if match else text


def _best_value_row(rows: list[Evidence], value_type: str, feature: str, feature_id: object) -> Evidence | None:
    typed_rows = [row for row in rows if row.element_type == value_type and row.id != feature_id]
    if not typed_rows:
        return None
    feature_terms = {
        "Fluid Active CPU": ("cpu", "compute", "hour"),
        "Firewall Rate Limit Requests": ("firewall", "allowed", "request"),
    }.get(feature, tuple(feature.lower().split()))
    related_rows = [
        row for row in typed_rows
        if any(term in row.text.lower() for term in feature_terms)
    ]
    return (related_rows or typed_rows)[0]


def group_evidence(rows: list[Evidence]) -> list[EvidenceGroupCandidate]:
    """Create deterministic feature groups from nearby raw evidence rows."""

    candidates: dict[tuple[str, str], EvidenceGroupCandidate] = {}
    feature_rows: dict[tuple[str, str], Evidence] = {}
    for row in rows:
        feature = _feature_name(row)
        if not feature:
            continue
        key = (str(row.page_id), feature)
        current = feature_rows.get(key)
        if current is None or (len(row.text), row.position) < (len(current.text), current.position):
            feature_rows[key] = row

    for feature_row in feature_rows.values():
        feature = _feature_name(feature_row)
        section = _normalized_section(feature_row, feature)
        nearby = sorted(
            [
                row
                for row in rows
                if row.page_id == feature_row.page_id
                and abs(row.position - feature_row.position) <= 5
            ],
            key=lambda row: (abs(row.position - feature_row.position), row.position),
        )
        limit_row = _best_value_row(nearby, "limit", feature, feature_row.id)
        pricing_row = _best_value_row(nearby, "pricing", feature, feature_row.id)
        related = list(
            {
                row.id: row
                for row in (feature_row, limit_row, pricing_row)
                if row is not None
            }.values()
        )
        candidates[(str(feature_row.page_id), feature)] = EvidenceGroupCandidate(
            section=section,
            feature=feature,
            limit=_value_snippet(limit_row.text, "limit") if limit_row else _value_snippet(feature_row.text, "limit") if "included" in feature_row.text.lower() else None,
            pricing=_value_snippet(pricing_row.text, "pricing") if pricing_row else _value_snippet(feature_row.text, "pricing") if "$" in feature_row.text else None,
            evidence=related,
        )
    return list(candidates.values())