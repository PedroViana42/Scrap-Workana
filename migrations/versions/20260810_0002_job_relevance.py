"""job relevance fields

Revision ID: 20260810_0002
Revises: 20260810_0001
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260810_0002"
down_revision = "20260810_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("relevance_score", sa.Integer(), nullable=True))
    op.add_column("jobs", sa.Column("relevance_band", sa.String(length=30), nullable=True))
    op.add_column("jobs", sa.Column("relevance_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("jobs", sa.Column("relevance_components", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("jobs", sa.Column("relevance_version", sa.String(length=80), nullable=True))
    op.add_column("jobs", sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_jobs_jobs_relevance_score_range",
        "jobs",
        "relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 100)",
    )
    op.create_index("ix_jobs_active_relevance_score", "jobs", ["active", "relevance_score"])


def downgrade() -> None:
    op.drop_index("ix_jobs_active_relevance_score", table_name="jobs")
    op.drop_constraint("ck_jobs_jobs_relevance_score_range", "jobs", type_="check")
    op.drop_column("jobs", "scored_at")
    op.drop_column("jobs", "relevance_version")
    op.drop_column("jobs", "relevance_components")
    op.drop_column("jobs", "relevance_reasons")
    op.drop_column("jobs", "relevance_band")
    op.drop_column("jobs", "relevance_score")

