"""
Structured logging setup for StyleSense.

We use Python's built-in logging with a consistent format so that
log lines are easy to read locally and easy to parse in production
(e.g., on Render's log viewer).
"""

import logging
import sys
from flask import Flask


def setup_logger(app: Flask) -> None:
    """
    Configure the Flask app logger with a structured format.

    Args:
        app: The Flask application instance.
    """
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)

    # Also configure the root logger so pymongo warnings appear cleanly
    logging.getLogger("pymongo").setLevel(logging.WARNING)
