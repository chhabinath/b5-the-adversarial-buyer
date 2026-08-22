"""URL normalization and same-domain link discovery."""

from collections.abc import Iterable
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit


PRIORITY_TERMS = (
    "pricing",
    "plans",
    "features",
    "security",
    "compliance",
    "integrations",
    "customers",
    "case-stud",
    "faq",
    "documentation",
    "docs",
    "api",
    "enterprise",
)


def normalize_url(url: str) -> str:
    """Normalize a web URL for comparison and crawling."""

    without_fragment, _ = urldefrag(url.strip())
    parsed = urlsplit(without_fragment)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    if parsed.port and parsed.port not in (80, 443):
        hostname = f"{hostname}:{parsed.port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, hostname, path, parsed.query, ""))


def is_same_domain(url: str, root_url: str) -> bool:
    """Return whether a URL belongs to the root hostname."""

    return (urlsplit(url).hostname or "").lower() == (urlsplit(root_url).hostname or "").lower()


def discover_links(html: str, current_url: str, root_url: str) -> list[str]:
    """Extract unique HTTP(S) same-domain links from a page."""

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        candidate = urljoin(current_url, anchor["href"])
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"}:
            continue
        normalized = normalize_url(candidate)
        if is_same_domain(normalized, root_url):
            links.add(normalized)
    return sorted(links, key=page_priority)


def page_priority(url: str) -> tuple[int, str]:
    """Sort relevant pages ahead of generic pages deterministically."""

    lowered = url.lower()
    priority = next((index for index, term in enumerate(PRIORITY_TERMS) if term in lowered), len(PRIORITY_TERMS))
    return priority, lowered


def prioritize_urls(urls: Iterable[str]) -> list[str]:
    """Return normalized, unique URLs in crawl priority order."""

    return sorted({normalize_url(url) for url in urls}, key=page_priority)