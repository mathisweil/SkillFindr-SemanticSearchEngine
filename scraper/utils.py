import json
import logging
import os
from selenium import webdriver


def load_config():
    """Loads the configuration from the config.json file."""
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, "config.json")

        with open(config_path, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print("Error: config.json file not found.")
        exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in config.json.")
        exit(1)


def setup_logger(config):
    """Sets up the logger for the scraper."""
    log_path = config.get("log_path", "./logs/scraper.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)  # Ensure the logs directory exists

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Logger initialised.")


def init_driver(config):
    """Initializes the Chrome WebDriver with options."""
    options = webdriver.ChromeOptions()

    webdriver_args = config.get("webdriver_args", {})
    if webdriver_args.get("headless"):
        options.add_argument("--headless")

    logging.info("Chrome WebDriver initialised.")
    return webdriver.Chrome(options=options)