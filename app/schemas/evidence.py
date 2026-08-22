"""Schemas for extracted website evidence."""

from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field


class EvidenceResponse(BaseModel):
    id: UUID
    page_id: UUID
    page_url: AnyHttpUrl
    page_title: str
    section: str
    text: str
    element_type: str
    position: int = Field(ge=0)


class EvidenceExtractionResponse(BaseModel):
    project_id: UUID
    evidence: list[EvidenceResponse]
    groups: list["EvidenceGroupResponse"] = Field(default_factory=list)


class EvidenceGroupResponse(BaseModel):
    id: UUID
    section: str
    feature: str
    limit: str | None
    pricing: str | None
    evidence_ids: list[UUID]