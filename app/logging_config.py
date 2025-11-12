import logging
import os

from .config import settings


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", settings.log.level).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
