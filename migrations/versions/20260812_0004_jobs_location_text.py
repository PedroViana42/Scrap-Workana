"""expand job location length

Revision ID: 20260812_0004
Revises: 20260812_0003
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260812_0004"
down_revision = "20260812_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "jobs",
        "location",
        existing_type=sa.String(length=240),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "jobs",
        "location",
        existing_type=sa.Text(),
        type_=sa.String(length=240),
        existing_nullable=True,
    )
