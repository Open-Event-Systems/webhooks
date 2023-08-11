"""Logging module."""
import logging
import sys

from loguru import logger
from oes.util.logging import InterceptHandler


def setup_logging(debug: bool = False):
    """Set up the logger."""
    level = logging.DEBUG if debug else logging.INFO

    logger.remove()
    logger.add(sys.stderr, level=level)

    logging.basicConfig(handlers=[InterceptHandler()], level=level, force=True)
