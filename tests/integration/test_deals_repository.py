from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from radar.database.models.price_history import PriceHistoryDB
from radar.database.repositories.deals import DealRepository
from radar.database.repositories.sources import sync_source_catalog
from radar.models import Deal


pytestmark = pytest.mark.integration


def _deal(price=Decimal("100.00"), collected_at=None):
    return Deal(
        source="amazon",
        external_id="deal-1",
        title="Keyboard",
        description="Mechanical keyboard",
        url="https://example.com/deal/1",
        store="Amazon",
        price=price,
        original_price=Decimal("150.00"),
        currency="BRL",
        collected_at=collected_at or datetime.now(timezone.utc),
    )


def test_new_deal_creates_price_history(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = DealRepository(db_session)

    deal, created, price_history_created = repository.upsert(_deal())
    db_session.commit()

    assert created is True
    assert price_history_created is True
    assert deal.price == Decimal("100.00")
    assert db_session.query(PriceHistoryDB).count() == 1


def test_same_price_does_not_create_redundant_history(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = DealRepository(db_session)

    repository.upsert(_deal())
    db_session.commit()
    _, created_again, price_history_created = repository.upsert(_deal())
    db_session.commit()

    assert created_again is False
    assert price_history_created is False
    assert db_session.query(PriceHistoryDB).count() == 1


def test_changed_price_updates_deal_and_creates_history_point(db_session):
    sync_source_catalog(db_session)
    db_session.commit()
    repository = DealRepository(db_session)
    first_time = datetime(2026, 8, 10, 10, tzinfo=timezone.utc)

    repository.upsert(_deal(price=Decimal("100.00"), collected_at=first_time))
    db_session.commit()
    deal, created_again, price_history_created = repository.upsert(
        _deal(price=Decimal("90.00"), collected_at=first_time + timedelta(hours=1))
    )
    db_session.commit()

    assert created_again is False
    assert price_history_created is True
    assert deal.price == Decimal("90.00")
    assert db_session.query(PriceHistoryDB).count() == 2

