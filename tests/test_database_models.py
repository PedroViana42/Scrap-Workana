from decimal import Decimal

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from radar.database.base import Base
from radar.database.models.company_source import CompanySourceDB
from radar.database.models.deal import DealDB
from radar.database.models.job import JobDB
from radar.database.models.price_history import PriceHistoryDB
from radar.database.models.scrape_run import ScrapeRunDB
from radar.database.models.source import SourceDB


def test_database_metadata_contains_expected_tables():
    assert {
        "sources",
        "company_sources",
        "jobs",
        "deals",
        "price_history",
        "scrape_runs",
    }.issubset(Base.metadata.tables)


def test_sources_constraints_and_jsonb_columns():
    table = SourceDB.__table__
    unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("name",) in unique_columns
    assert isinstance(table.c.capabilities.type, JSONB)
    assert isinstance(table.c.metadata.type, JSONB)


def test_company_sources_unique_identifier_per_source_and_jsonb_tags():
    table = CompanySourceDB.__table__
    unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("source_id", "external_identifier") in unique_columns
    assert isinstance(table.c.tags.type, JSONB)


def test_jobs_constraints_indexes_and_numeric_money():
    table = JobDB.__table__
    indexes = {index.name: index for index in table.indexes}

    assert table.c.fingerprint.unique is True
    assert "ix_jobs_source_id" in indexes
    assert "ix_jobs_published_at" in indexes
    assert "ix_jobs_collected_at" in indexes
    assert "ix_jobs_active" in indexes
    assert "ix_jobs_company_source_id" in indexes
    assert indexes["uq_jobs_source_external_id_not_null"].unique is True
    assert isinstance(table.c.technologies.type, ARRAY)
    assert indexes["ix_jobs_technologies_gin"].dialect_options["postgresql"]["using"] == "gin"
    assert table.c.salary_min.type.asdecimal is True
    assert table.c.salary_min.type.precision == 14
    assert table.c.salary_min.type.scale == 2


def test_deals_constraints_indexes_and_numeric_money():
    table = DealDB.__table__
    indexes = {index.name: index for index in table.indexes}

    assert table.c.fingerprint.unique is True
    assert "ix_deals_source_id" in indexes
    assert "ix_deals_published_at" in indexes
    assert "ix_deals_collected_at" in indexes
    assert "ix_deals_active" in indexes
    assert "ix_deals_store" in indexes
    assert indexes["uq_deals_source_external_id_not_null"].unique is True
    assert table.c.price.type.asdecimal is True


def test_price_history_and_scrape_run_indexes():
    price_indexes = {index.name for index in PriceHistoryDB.__table__.indexes}
    scrape_indexes = {index.name for index in ScrapeRunDB.__table__.indexes}

    assert "ix_price_history_deal_captured_at" in price_indexes
    assert "ix_scrape_runs_source_id" in scrape_indexes


def test_bigint_identity_primary_keys_are_used():
    for model in [SourceDB, CompanySourceDB, JobDB, DealDB, PriceHistoryDB, ScrapeRunDB]:
        id_column = model.__table__.c.id
        assert id_column.primary_key is True
        assert id_column.identity is not None

