import logging

from utils.config import load_config
from scrapers.IBM_scraper import IBMScraper

from utils.selenium_utils import init_driver
from utils.io_utils import save_to_csv, save_to_json


if __name__ == '__main__':
    config = load_config()
    logging.basicConfig(
        filename=config["log_path"],
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    with init_driver(config) as driver:
        driver.get(config["login_url"])
        logging.info(f"Navigated to {config['login_url']}.")

        scraper = IBMScraper(driver, config)
        scraper.login()

        if courses := scraper.scrape_courses():
            if config.get("output_formats", {}).get("json"):
                save_to_json(courses, f"{config['output_path']}/{config['search_keyword']}")
            if config.get("output_formats", {}).get("csv"):
                save_to_csv(courses, f"{config['output_path']}/{config['search_keyword']}")