import os
import logging


def setup_logger(config):
    """Sets up the logger for the scrapers."""
    log_path = config.get("log_path", "./logs/scrapers.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)  # Ensure the logs directory exists

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Logger initialised.")