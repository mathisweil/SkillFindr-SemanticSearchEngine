import logging
import pandas as pd
from datetime import datetime

from utils.config import load_config
from scrapers.IBM_scraper import IBMScraper

from utils.selenium_utils import init_driver


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

        if not courses:
            logging.warning("No courses to process.")
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            df = pd.DataFrame(courses)

            csv_filename = f"{config['raw_output_path']}/{config['output_filename']}_{current_date}.csv"
            json_filename = f"{config['raw_output_path']}/{config['output_filename']}_{current_date}.json"

            df.to_csv(csv_filename, index=True)
            df.to_json(json_filename, orient="records", indent=4)
            logging.info(f"Data successfully saved")
