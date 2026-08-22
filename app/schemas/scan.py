"""Schemas for website scans."""

from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class ScanRequest(BaseModel):
    """Input required to start a website scan."""

    website_url: AnyHttpUrl

    @field_validator("website_url")
    @classmethod
    def reject_unsupported_schemes(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme not in {"http", "https"}:
            raise ValueError("website_url must use http or https")
        return value


class DiscoveredPage(BaseModel):
    """A crawled page returned by the Phase 2 scan."""

    url: AnyHttpUrl
    title: str
    content: str
    crawl_order: int = Field(ge=0)


class ScanResponse(BaseModel):
    """Scan result containing discovered pages."""

    project_id: UUID
    status: str
    pages: list[DiscoveredPage]

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": "replace-with-project-id-from-this-response",
                "status": "COMPLETED",
                "pages": [],
            }
        }
    }