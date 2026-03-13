"""
Logging configuration for the trading bot.
Sets up structured logging to both console and file.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return the root logger for the trading bot.

    Sets up:
    - A rotating file handler writing to logs/trading_bot.log
    - A console (stream) handler for terminal output

    Args:
        log_level: Logging level string, e.g. "INFO", "DEBUG".

    Returns:
        Configured root logger instance.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(numeric_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Rotating file handler — max 5 MB, keep 3 backups
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # only warnings+ to console
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the 'trading_bot' namespace.

    Args:
        name: Sub-logger name (e.g. 'client', 'orders').

    Returns:
        Child logger instance.
    """
    return logging.getLogger(f"trading_bot.{name}")
