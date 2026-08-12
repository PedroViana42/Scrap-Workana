"""scheduler lifecycle metadata

Revision ID: 20260812_0003
Revises: 20260810_0002
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260812_0003"
down_revision = "20260810_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scrape_runs", sa.Column("company_source_id", sa.BigInteger(), nullable=True))
    op.add_column("scrape_runs", sa.Column("items_deactivated", sa.Integer(), nullable=False, server_default="0"))
    op.create_foreign_key(
        op.f("fk_scrape_runs_company_source_id_company_sources"),
        "scrape_runs",
        "company_sources",
        ["company_source_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_scrape_runs_company_source_id"), "scrape_runs", ["company_source_id"])
    op.create_index("ix_scrape_runs_company_source_started_at", "scrape_runs", ["company_source_id", "started_at"])
    op.alter_column("scrape_runs", "items_deactivated", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_scrape_runs_company_source_started_at", table_name="scrape_runs")
    op.drop_index(op.f("ix_scrape_runs_company_source_id"), table_name="scrape_runs")
    op.drop_constraint(op.f("fk_scrape_runs_company_source_id_company_sources"), "scrape_runs", type_="foreignkey")
    op.drop_column("scrape_runs", "items_deactivated")
    op.drop_column("scrape_runs", "company_source_id")
    op.drop_column("jobs", "deactivated_at")
