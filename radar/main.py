import logging

from radar.logging_config import configure_logging


logger = logging.getLogger(__name__)


def main() -> int:
    configure_logging()
    logger.info("Radar ainda não possui collectors ativos configurados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
