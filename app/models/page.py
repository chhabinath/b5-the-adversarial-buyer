"""Crawled page database model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(1000), default="")
    page_type: Mapped[str] = mapped_column(String(40), default="OTHER")
    content: Mapped[str] = mapped_column(Text)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    crawl_order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    project: Mapped["Project"] = relationship(back_populates="pages")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="page", cascade="all, delete-orphan")