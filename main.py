import logging

from utils.config import load_config
from scrapers.IBM_scraper import IBMScraper

from utils.selenium_utils import init_driver
from utils.data_processing import process_with_pandas


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

        courses = scraper.scrape_courses()

        process_with_pandas(courses, f"{config['output_path']}/{config['search_keyword']}")
