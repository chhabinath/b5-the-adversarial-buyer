"""Website scan API."""

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.crawler.crawl4ai_client import crawl_website
from app.extraction.evidence_extractor import extract_evidence
from app.extraction.evidence_grouping import group_evidence
from app.models.evidence import Evidence
from app.models.evidence_group import EvidenceGroup, evidence_group_members
from app.models.page import Page
from app.models.project import Project, ProjectStatus
from app.schemas.evidence import EvidenceExtractionResponse, EvidenceGroupResponse, EvidenceResponse
from app.schemas.scan import DiscoveredPage, ScanRequest, ScanResponse


router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


@router.post("", response_model=ScanResponse, status_code=200)
async def start_scan(request: ScanRequest, db: Session = Depends(get_db)) -> ScanResponse:
    """Crawl a public website and return its discovered pages."""

    settings = get_settings()
    try:
        pages = await crawl_website(str(request.website_url), settings.max_pages)
    except Exception as error:
        raise HTTPException(status_code=502, detail="Website crawl failed") from error
    if not pages:
        raise HTTPException(status_code=502, detail="No readable pages found")
    project = Project(
        company_name="Unknown company",
        website_url=str(request.website_url),
        status=ProjectStatus.COMPLETED.value,
    )
    project.pages = [
        Page(
            url=page.url,
            title=page.title,
            content=page.content,
            crawl_order=page.crawl_order,
            raw_html=page.raw_html or None,
        )
        for page in pages
    ]
    db.add(project)
    db.commit()
    db.refresh(project)
    return ScanResponse(
        project_id=project.id,
        status="COMPLETED",
        pages=[
            DiscoveredPage(
                url=page.url,
                title=page.title,
                content=page.content,
                crawl_order=page.crawl_order,
            )
            for page in pages
        ],
    )


@router.post(
    "/{project_id}/evidence",
    response_model=EvidenceExtractionResponse,
    summary="Extract evidence for a completed scan",
    description="Use the project_id returned by POST /api/v1/scans. The Swagger placeholder UUID is not a real project.",
)
async def extract_project_evidence(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> EvidenceExtractionResponse:
    """Extract and persist atomic evidence for a completed crawl."""

    project = db.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise HTTPException(status_code=404, detail="Scan project not found")

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        for page in project.pages:
            if page.raw_html:
                continue
            try:
                response = await client.get(page.url)
                response.raise_for_status()
                if "text/html" in response.headers.get("content-type", "").lower():
                    page.raw_html = response.text
            except httpx.HTTPError:
                continue

    evidence_rows: list[Evidence] = []
    for page in project.pages:
        page.evidence.clear()
        evidence_rows.extend(
            Evidence(
                page_id=page.id,
                section=unit.section,
                text=unit.text,
                element_type=unit.element_type,
                position=unit.position,
            )
            for unit in extract_evidence(page.url, page.content, page.raw_html)
        )
    db.add_all(evidence_rows)
    db.commit()
    existing_group_ids = select(EvidenceGroup.id).where(EvidenceGroup.project_id == project.id)
    db.execute(delete(evidence_group_members).where(evidence_group_members.c.group_id.in_(existing_group_ids)))
    for existing_group in db.scalars(select(EvidenceGroup).where(EvidenceGroup.project_id == project.id)).all():
        db.delete(existing_group)
    db.flush()
    group_rows = [
        EvidenceGroup(
            project_id=project.id,
            section=candidate.section,
            feature=candidate.feature,
            limit=candidate.limit,
            pricing=candidate.pricing,
            evidence=candidate.evidence,
        )
        for candidate in group_evidence(evidence_rows)
    ]
    db.add_all(group_rows)
    db.commit()
    project.status = ProjectStatus.ANALYZING.value
    db.commit()
    return EvidenceExtractionResponse(
        project_id=project.id,
        evidence=[
            EvidenceResponse(
                id=row.id,
                page_id=row.page_id,
                page_url=next(page.url for page in project.pages if page.id == row.page_id),
                page_title=next(page.title for page in project.pages if page.id == row.page_id),
                section=row.section,
                text=row.text,
                element_type=row.element_type,
                position=row.position,
            )
            for row in evidence_rows
        ],
        groups=[
            EvidenceGroupResponse(
                id=group.id,
                section=group.section,
                feature=group.feature,
                limit=group.limit,
                pricing=group.pricing,
                evidence_ids=[row.id for row in group.evidence],
            )
            for group in group_rows
        ],
    )