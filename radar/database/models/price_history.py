from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from radar.database.base import Base


class PriceHistoryDB(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_deal_captured_at", "deal_id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    deal = relationship("DealDB", back_populates="price_history")

