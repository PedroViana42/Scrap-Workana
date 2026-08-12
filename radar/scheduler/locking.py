from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection


SCHEDULER_LOCK_KEY = 774_271_001


class RadarSchedulerLock:
    def __init__(self, engine: Engine, lock_key: int = SCHEDULER_LOCK_KEY) -> None:
        self.engine = engine
        self.lock_key = lock_key
        self.connection: Connection | None = None
        self.acquired = False

    def acquire(self) -> bool:
        if self.connection is None:
            self.connection = self.engine.connect()
        acquired = bool(
            self.connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_key)"),
                {"lock_key": self.lock_key},
            ).scalar_one()
        )
        self.acquired = acquired
        return acquired

    def release(self) -> None:
        if self.connection is None:
            return
        try:
            if self.acquired:
                self.connection.execute(text("SELECT pg_advisory_unlock(:lock_key)"), {"lock_key": self.lock_key})
        finally:
            self.acquired = False
            self.connection.close()
            self.connection = None

    def __enter__(self) -> "RadarSchedulerLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.release()
