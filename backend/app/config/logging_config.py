"""
Application-wide logging configuration using loguru.
Logs to console (structured) and to a rotating file under /app/logs.
"""

import sys
import os
from loguru import logger

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def configure_logging():
    logger.remove()  # remove default handler

    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    logger.add(
        os.path.join(LOG_DIR, "app.log"),
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} - {message}",
    )

    return logger


app_logger = configure_logging()
