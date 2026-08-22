"""Atomic website evidence database model."""

from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    page_id: Mapped[UUID] = mapped_column(ForeignKey("pages.id"), index=True)
    section: Mapped[str] = mapped_column(String(500), default="Page")
    text: Mapped[str] = mapped_column(Text)
    element_type: Mapped[str] = mapped_column(String(40), default="paragraph")
    position: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    page: Mapped["Page"] = relationship(back_populates="evidence")