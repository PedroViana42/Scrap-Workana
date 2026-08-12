from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass
class Deal:
    source: str
    title: str
    url: str
    external_id: str | None = None
    description: str | None = None
    image_url: str | None = None
    store: str | None = None
    price: Decimal | None = None
    original_price: Decimal | None = None
    currency: str | None = None
    coupon: str | None = None
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
