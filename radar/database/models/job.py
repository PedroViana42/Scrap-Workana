from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from radar.database.base import Base


class JobDB(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_source_id", "source_id"),
        Index("ix_jobs_company_source_id", "company_source_id"),
        Index("ix_jobs_published_at", "published_at"),
        Index("ix_jobs_collected_at", "collected_at"),
        Index("ix_jobs_active", "active"),
        Index("ix_jobs_source_external_id", "source_id", "external_id"),
        Index("uq_jobs_source_external_id_not_null", "source_id", "external_id", unique=True, postgresql_where=text("external_id IS NOT NULL")),
        Index("ix_jobs_technologies_gin", "technologies", postgresql_using="gin"),
        Index("ix_jobs_active_relevance_score", "active", "relevance_score"),
        CheckConstraint("relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 100)", name="jobs_relevance_score_range"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    company_source_id: Mapped[int | None] = mapped_column(ForeignKey("company_sources.id", ondelete="SET NULL"))
    external_id: Mapped[str | None] = mapped_column(String(240))
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str | None] = mapped_column(String(240))
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text)
    remote_type: Mapped[str] = mapped_column(String(30), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    seniority: Mapped[str] = mapped_column(String(30), nullable=False)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    salary_currency: Mapped[str | None] = mapped_column(String(3))
    technologies: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    relevance_score: Mapped[int | None] = mapped_column(Integer)
    relevance_band: Mapped[str | None] = mapped_column(String(30))
    relevance_reasons: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    relevance_components: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    relevance_version: Mapped[str | None] = mapped_column(String(80))
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    source = relationship("SourceDB", back_populates="jobs")
    company_source = relationship("CompanySourceDB", back_populates="jobs")
