from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from radar.database.base import Base


class SourceDB(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collector: Mapped[str | None] = mapped_column(String(120))
    base_url: Mapped[str | None] = mapped_column(Text)
    interval_minutes: Mapped[int | None] = mapped_column(Integer)
    requires_browser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_auth: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    company_sources = relationship("CompanySourceDB", back_populates="source")
    jobs = relationship("JobDB", back_populates="source")
    deals = relationship("DealDB", back_populates="source")
    scrape_runs = relationship("ScrapeRunDB", back_populates="source")

