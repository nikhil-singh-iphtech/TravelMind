import logging

from app.core.config import settings


def configure_logging() -> None:
    """
    Sets up a single, consistent logging format for the whole app.

    Called once at startup from main.py. Every module can then do:
        logger = logging.getLogger(__name__)
    and get the same formatting/level without reconfiguring anything.
    """
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )