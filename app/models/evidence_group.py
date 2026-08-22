"""Grouped relationships between raw evidence records."""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


evidence_group_members = Table(
    "evidence_group_members",
    Base.metadata,
    Column("group_id", ForeignKey("evidence_groups.id"), primary_key=True),
    Column("evidence_id", ForeignKey("evidence.id"), primary_key=True),
)


class EvidenceGroup(Base):
    __tablename__ = "evidence_groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    section: Mapped[str] = mapped_column(String(500))
    feature: Mapped[str] = mapped_column(String(500))
    limit: Mapped[str | None] = mapped_column(Text, nullable=True)
    pricing: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence: Mapped[list["Evidence"]] = relationship(secondary=evidence_group_members)