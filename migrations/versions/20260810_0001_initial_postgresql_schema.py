"""initial postgresql schema

Revision ID: 20260810_0001
Revises:
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260810_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("content_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("collector", sa.String(length=120), nullable=True),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("interval_minutes", sa.Integer(), nullable=True),
        sa.Column("requires_browser", sa.Boolean(), nullable=False),
        sa.Column("requires_auth", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint("name", name=op.f("uq_sources_name")),
    )

    op.create_table(
        "company_sources",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("company_name", sa.String(length=240), nullable=False),
        sa.Column("external_identifier", sa.String(length=240), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name=op.f("fk_company_sources_source_id_sources"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_sources")),
        sa.UniqueConstraint("source_id", "external_identifier", name="uq_company_sources_source_external_identifier"),
    )
    op.create_index(op.f("ix_company_sources_source_id"), "company_sources", ["source_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("company_source_id", sa.BigInteger(), nullable=True),
        sa.Column("external_id", sa.String(length=240), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("company", sa.String(length=240), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=240), nullable=True),
        sa.Column("remote_type", sa.String(length=30), nullable=False),
        sa.Column("employment_type", sa.String(length=30), nullable=False),
        sa.Column("seniority", sa.String(length=30), nullable=False),
        sa.Column("salary_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=True),
        sa.Column("technologies", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_source_id"], ["company_sources.id"], name=op.f("fk_jobs_company_source_id_company_sources"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name=op.f("fk_jobs_source_id_sources"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("fingerprint", name=op.f("uq_jobs_fingerprint")),
    )
    op.create_index("ix_jobs_active", "jobs", ["active"])
    op.create_index("ix_jobs_collected_at", "jobs", ["collected_at"])
    op.create_index("ix_jobs_company_source_id", "jobs", ["company_source_id"])
    op.create_index("ix_jobs_published_at", "jobs", ["published_at"])
    op.create_index("ix_jobs_source_external_id", "jobs", ["source_id", "external_id"])
    op.create_index("ix_jobs_source_id", "jobs", ["source_id"])
    op.create_index("ix_jobs_technologies_gin", "jobs", ["technologies"], postgresql_using="gin")
    op.create_index("uq_jobs_source_external_id_not_null", "jobs", ["source_id", "external_id"], unique=True, postgresql_where=sa.text("external_id IS NOT NULL"))

    op.create_table(
        "deals",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("external_id", sa.String(length=240), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("store", sa.String(length=240), nullable=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=True),
        sa.Column("original_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("coupon", sa.String(length=120), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name=op.f("fk_deals_source_id_sources"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deals")),
        sa.UniqueConstraint("fingerprint", name=op.f("uq_deals_fingerprint")),
    )
    op.create_index("ix_deals_active", "deals", ["active"])
    op.create_index("ix_deals_collected_at", "deals", ["collected_at"])
    op.create_index("ix_deals_published_at", "deals", ["published_at"])
    op.create_index("ix_deals_source_external_id", "deals", ["source_id", "external_id"])
    op.create_index("ix_deals_source_id", "deals", ["source_id"])
    op.create_index("ix_deals_store", "deals", ["store"])
    op.create_index("uq_deals_source_external_id_not_null", "deals", ["source_id", "external_id"], unique=True, postgresql_where=sa.text("external_id IS NOT NULL"))

    op.create_table(
        "price_history",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("deal_id", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], name=op.f("fk_price_history_deal_id_deals"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_history")),
    )
    op.create_index("ix_price_history_deal_captured_at", "price_history", ["deal_id", "captured_at"])

    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("items_found", sa.Integer(), nullable=False),
        sa.Column("items_new", sa.Integer(), nullable=False),
        sa.Column("items_updated", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(length=240), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name=op.f("fk_scrape_runs_source_id_sources"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scrape_runs")),
    )
    op.create_index(op.f("ix_scrape_runs_source_id"), "scrape_runs", ["source_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_scrape_runs_source_id"), table_name="scrape_runs")
    op.drop_table("scrape_runs")
    op.drop_index("ix_price_history_deal_captured_at", table_name="price_history")
    op.drop_table("price_history")
    op.drop_index("uq_deals_source_external_id_not_null", table_name="deals")
    op.drop_index("ix_deals_store", table_name="deals")
    op.drop_index("ix_deals_source_id", table_name="deals")
    op.drop_index("ix_deals_source_external_id", table_name="deals")
    op.drop_index("ix_deals_published_at", table_name="deals")
    op.drop_index("ix_deals_collected_at", table_name="deals")
    op.drop_index("ix_deals_active", table_name="deals")
    op.drop_table("deals")
    op.drop_index("uq_jobs_source_external_id_not_null", table_name="jobs")
    op.drop_index("ix_jobs_technologies_gin", table_name="jobs")
    op.drop_index("ix_jobs_source_id", table_name="jobs")
    op.drop_index("ix_jobs_source_external_id", table_name="jobs")
    op.drop_index("ix_jobs_published_at", table_name="jobs")
    op.drop_index("ix_jobs_company_source_id", table_name="jobs")
    op.drop_index("ix_jobs_collected_at", table_name="jobs")
    op.drop_index("ix_jobs_active", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_company_sources_source_id"), table_name="company_sources")
    op.drop_table("company_sources")
    op.drop_table("sources")

