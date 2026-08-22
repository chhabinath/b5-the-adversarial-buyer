from fastapi.testclient import TestClient

from app.api import scan as scan_api
from app.core.database import Base, engine
from app.crawler.crawl4ai_client import CrawledPage
from app.main import app


async def fake_crawl_website(_: str, __: int) -> list[CrawledPage]:
    return [
        CrawledPage(
            url="https://vercel.com/pricing",
            title="Example",
            content="Example website content.",
            crawl_order=0,
            raw_html="<html><body><nav>Navigation noise</nav><main><h1>Pricing</h1><p>Pro costs $20 per month.</p><p>Includes team collaboration.</p></main><footer>Footer noise</footer></body></html>",
        )
    ]


def test_start_scan_returns_discovered_pages(monkeypatch) -> None:
    monkeypatch.setattr(scan_api, "crawl_website", fake_crawl_website)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/scans",
            json={"website_url": "https://example.com"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["pages"][0]["url"] == "https://vercel.com/pricing"
    assert body["pages"][0]["content"] == "Example website content."

    with TestClient(app) as client:
        evidence_response = client.post(f"/api/v1/scans/{body['project_id']}/evidence")

    assert evidence_response.status_code == 200
    evidence_body = evidence_response.json()
    assert evidence_body["project_id"] == body["project_id"]
    assert evidence_body["evidence"][0]["text"] == "Pro costs $20 per month."
    assert evidence_body["evidence"][0]["element_type"] == "pricing"
    assert evidence_body["evidence"][0]["page_url"] == "https://vercel.com/pricing"
    assert all("Navigation noise" not in item["text"] for item in evidence_body["evidence"])
    assert all("Footer noise" not in item["text"] for item in evidence_body["evidence"])