from sqlalchemy import select
from sqlalchemy.orm import Session

from radar.database.models.deal import DealDB
from radar.database.models.price_history import PriceHistoryDB
from radar.database.repositories.mappers import deal_to_values
from radar.database.repositories.sources import SourceRepository
from radar.models.deal import Deal
from radar.services.deduplication import generate_fingerprint


class DealRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.sources = SourceRepository(session)

    def get_by_fingerprint(self, fingerprint: str) -> DealDB | None:
        return self.session.scalar(select(DealDB).where(DealDB.fingerprint == fingerprint))

    def get_by_external_id(self, source_id: int, external_id: str | None) -> DealDB | None:
        if not external_id:
            return None
        return self.session.scalar(
            select(DealDB).where(DealDB.source_id == source_id, DealDB.external_id == external_id)
        )

    def upsert(self, deal: Deal, raw_data: dict | None = None) -> tuple[DealDB, bool, bool]:
        source = self.sources.get_by_name(deal.source)
        if source is None:
            raise ValueError(f"Source not found for deal: {deal.source}")

        fingerprint = generate_fingerprint(
            source=deal.source,
            external_id=deal.external_id,
            url=deal.url,
            title=deal.title,
            company=deal.store,
        )
        existing = self.get_by_external_id(source.id, deal.external_id) or self.get_by_fingerprint(fingerprint)
        values = deal_to_values(deal, source.id, fingerprint)
        if raw_data is not None:
            values["raw_data"] = raw_data

        price_changed = False
        if existing is None:
            values["first_seen_at"] = deal.collected_at
            existing = DealDB(**values)
            self.session.add(existing)
            self.session.flush()
            if existing.price is not None:
                self.session.add(PriceHistoryDB(deal_id=existing.id, price=existing.price, captured_at=deal.collected_at))
            self.session.flush()
            return existing, True, existing.price is not None

        old_price = existing.price
        for field, value in values.items():
            if field == "first_seen_at":
                continue
            setattr(existing, field, value)

        price_changed = old_price != existing.price and existing.price is not None
        if price_changed:
            self.session.add(PriceHistoryDB(deal_id=existing.id, price=existing.price, captured_at=deal.collected_at))

        self.session.flush()
        return existing, False, price_changed

