"""Bounded website crawler used by the scan API."""

from dataclasses import dataclass
import logging
import httpx

from app.crawler.content_cleaner import extract_page_content
from app.crawler.page_discovery import discover_links, normalize_url, prioritize_urls

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CrawledPage:
    """A successfully fetched page and its provenance."""

    url: str
    title: str
    content: str
    crawl_order: int
    raw_html: str = ""


class Crawl4AIClient:
    """Crawl a bounded set of same-domain pages with async HTTP I/O."""

    def __init__(self, max_pages: int = 30, timeout_seconds: float = 15.0) -> None:
        self.max_pages = max(1, max_pages)
        self.timeout_seconds = timeout_seconds

    async def crawl(self, root_url: str) -> list[CrawledPage]:
        """Fetch the root page and prioritized same-domain links."""

        root_url = normalize_url(root_url)
        pending = [root_url]
        queued = {root_url}
        visited: set[str] = set()
        pages: list[CrawledPage] = []

        headers = {"User-Agent": "The-Adversarial-Buyer/0.1"}
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.timeout_seconds,
            headers=headers,
        ) as client:
            while pending and len(pages) < self.max_pages:
                url = pending.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                except (httpx.HTTPError, UnicodeError) as error:
                    logger.warning("page_crawl_failed", extra={"url": url, "error": str(error)})
                    continue
                if "text/html" not in response.headers.get("content-type", "").lower():
                    continue
                title, content = extract_page_content(response.text)
                if not content:
                    continue
                pages.append(
                    CrawledPage(
                        url=url,
                        title=title,
                        content=content,
                        crawl_order=len(pages),
                        raw_html=response.text,
                    )
                )
                discovered = discover_links(response.text, url, root_url)
                new_urls = [candidate for candidate in discovered if candidate not in queued and candidate not in visited]
                pending = prioritize_urls([*pending, *new_urls])
                queued.update(new_urls)
        return pages


async def crawl_website(root_url: str, max_pages: int = 30) -> list[CrawledPage]:
    """Convenience function for the scan route."""

    return await Crawl4AIClient(max_pages=max_pages).crawl(root_url)