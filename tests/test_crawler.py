import httpx
import pytest

from app.crawler.crawl4ai_client import Crawl4AIClient
from app.crawler.page_discovery import is_same_domain, normalize_url


def test_normalize_url_removes_fragment_and_trailing_slash() -> None:
    assert normalize_url("HTTPS://Example.com/pricing/#plans") == "https://example.com/pricing"


def test_same_domain_check_rejects_external_host() -> None:
    assert is_same_domain("https://example.com/docs", "https://example.com")
    assert not is_same_domain("https://other.example/docs", "https://example.com")


@pytest.mark.anyio
async def test_crawler_deduplicates_and_prioritizes_same_domain_pages() -> None:
    pages = {
        "https://example.com/": """
            <html><head><title>Home</title></head><body>
            <a href='/about/'>About</a><a href='/pricing#plans'>Pricing</a>
            <a href='https://other.example/nope'>External</a><a href='/pricing'>Duplicate</a>
            </body></html>
        """,
        "https://example.com/pricing": "<html><title>Pricing</title><p>Plans from $10 monthly.</p></html>",
        "https://example.com/about": "<html><title>About</title><p>About the company.</p></html>",
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        content = pages.get(str(request.url))
        if content is None:
            return httpx.Response(404)
        return httpx.Response(200, headers={"content-type": "text/html"}, text=content)

    client = Crawl4AIClient(max_pages=3)
    original_client = httpx.AsyncClient
    httpx.AsyncClient = lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs)  # type: ignore[method-assign]
    try:
        crawled = await client.crawl("https://example.com")
    finally:
        httpx.AsyncClient = original_client

    assert [page.url for page in crawled] == [
        "https://example.com/",
        "https://example.com/pricing",
        "https://example.com/about",
    ]