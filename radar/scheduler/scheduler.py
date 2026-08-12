from __future__ import annotations

import logging
import os
import signal
import time

from apscheduler.schedulers.background import BackgroundScheduler

from radar.database.session import create_db_engine, create_session_factory, session_scope
from radar.scheduler.cycle import run_scheduler_cycle, scheduler_poll_seconds
from radar.scheduler.locking import RadarSchedulerLock


logger = logging.getLogger(__name__)


class RadarScheduler:
    def __init__(self, database_url: str | None = None) -> None:
        self.engine = create_db_engine(database_url)
        self.session_factory = create_session_factory(self.engine)
        self.scheduler = BackgroundScheduler(timezone=os.getenv("RADAR_SCHEDULER_TIMEZONE", "UTC"))
        self.lock = RadarSchedulerLock(self.engine)
        self.shutdown_requested = False

    def start(self) -> int:
        if not self.lock.acquire():
            logger.error("scheduler_lock_unavailable")
            return 1

        poll_seconds = scheduler_poll_seconds()
        self.scheduler.add_job(self._run_cycle, "interval", seconds=poll_seconds, max_instances=1, coalesce=True)
        self.scheduler.start()
        logger.info("scheduler_started poll_seconds=%s", poll_seconds)
        self._install_signal_handlers()
        self._run_cycle()
        try:
            while not self.shutdown_requested:
                time.sleep(0.5)
        finally:
            self.stop()
        return 0

    def stop(self) -> None:
        self.shutdown_requested = True
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.lock.release()
        self.engine.dispose()
        logger.info("scheduler_stopped")

    def _run_cycle(self) -> None:
        if self.shutdown_requested:
            return
        with session_scope(self.session_factory) as session:
            run_scheduler_cycle(session)

    def _install_signal_handlers(self) -> None:
        def handle_signal(signum, frame) -> None:
            logger.info("scheduler_shutdown_requested signal=%s", signum)
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
