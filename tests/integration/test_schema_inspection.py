import pytest
from sqlalchemy import text


pytestmark = pytest.mark.integration


def test_real_schema_contains_expected_tables_and_indexes(db_session):
    table_names = set(
        db_session.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        ).scalars()
    )

    assert {
        "sources",
        "company_sources",
        "jobs",
        "deals",
        "price_history",
        "scrape_runs",
        "alembic_version",
    }.issubset(table_names)

    index_names = set(
        db_session.execute(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                """
            )
        ).scalars()
    )

    assert "uq_sources_name" in index_names
    assert "uq_jobs_fingerprint" in index_names
    assert "uq_deals_fingerprint" in index_names
    assert "ix_jobs_technologies_gin" in index_names
    assert "uq_jobs_source_external_id_not_null" in index_names
    assert "uq_deals_source_external_id_not_null" in index_names
    assert "ix_price_history_deal_captured_at" in index_names


def test_real_schema_contains_expected_foreign_keys(db_session):
    foreign_keys = set(
        db_session.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE contype = 'f'
                """
            )
        ).scalars()
    )

    assert "fk_jobs_source_id_sources" in foreign_keys
    assert "fk_deals_source_id_sources" in foreign_keys

