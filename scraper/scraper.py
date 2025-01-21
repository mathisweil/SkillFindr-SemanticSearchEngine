import time
import json
import logging
import os
from selenium import webdriver


def setup_logger():
    """Sets up the logger for the scraper."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_path, "logs", "scraper.log")

    os.makedirs(os.path.dirname(log_path), exist_ok=True)  # Ensure the logs directory exists

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Logger initialised.")

def load_config():
    """Loads the configuration from the config.json file."""
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, "config.json")

        with open(config_path, "r") as config_file:
            logging.info("Configuration file loaded successfully.")
            return json.load(config_file)
    except FileNotFoundError:
        logging.error("Error: config.json file not found.")
        print("Error: config.json file not found.")
        exit(1)
    except json.JSONDecodeError:
        logging.error("Error: Invalid JSON format in config.json.")
        print("Error: Invalid JSON format in config.json.")
        exit(1)

def init_driver():
    """Initializes the Chrome WebDriver with options."""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    logging.info("Chrome WebDriver initialised.")
    return webdriver.Chrome(options=options)

def scraper():
    logging.info("Scraper started.")
    config = load_config()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(config["login_url"])
        logging.info(f"Navigated to {config['login_url']}.")
        time.sleep(config["scrape_delay"])
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")
    finally:
        driver.quit()
        logging.info("WebDriver closed.")

if __name__ == '__main__':
    setup_logger()
    scraper()