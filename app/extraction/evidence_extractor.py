"""Convert crawled page text into atomic, source-linked evidence units."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ExtractedEvidence:
    """An evidence unit retaining its exact text position."""

    section: str
    text: str
    element_type: str
    position: int


def _section_for_url(url: str) -> str:
    path = urlsplit(url).path.strip("/")
    if not path:
        return "Home"
    return path.rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").title()


def _element_type(section: str, text: str) -> str:
    haystack = f"{section} {text}".lower()
    if "$" in text or "pricing" in haystack or "plan" in haystack or "billing" in haystack:
        return "pricing"
    if any(term in haystack for term in ("security", "compliance", "sso", "scim", "encryption", "gdpr")):
        return "security"
    if any(term in haystack for term in ("limit", "included", "per month", "monthly", "request", "seat")):
        return "limit"
    if any(term in haystack for term in ("integration", "api", "sdk", "webhook")):
        return "integration"
    return "feature"


def _extract_html_evidence(page_url: str, html: str) -> list[ExtractedEvidence]:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "template", "svg", "header", "nav", "footer", "aside", "form"]):
        element.decompose()
    root = soup.find("main") or soup.body or soup
    section = _section_for_url(page_url)
    units: list[ExtractedEvidence] = []
    seen: set[str] = set()
    for element in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "dt", "dd", "caption"]):
        text = " ".join(element.stripped_strings)
        if not text or text in seen:
            continue
        if element.name and element.name.startswith("h"):
            section = text
            continue
        if len(text) < 8:
            continue
        seen.add(text)
        units.append(
            ExtractedEvidence(
                section=section,
                text=text,
                element_type=_element_type(section, text),
                position=len(units),
            )
        )
    return units


def extract_evidence(page_url: str, content: str, raw_html: str | None = None) -> list[ExtractedEvidence]:
    """Extract exact, atomic evidence from semantic HTML elements.

    Stored readable text remains a compatibility fallback for scans created
    before raw HTML was persisted.
    """

    if raw_html:
        return _extract_html_evidence(page_url, raw_html)

    units: list[ExtractedEvidence] = []
    section = _section_for_url(page_url)
    for position, text in enumerate(part.strip() for part in content.split(".")):
        text = " ".join(text.split()).strip()
        if not text:
            continue
        units.append(
            ExtractedEvidence(
                section=section,
                text=text,
                element_type=_element_type(section, text),
                position=position,
            )
        )
    return units