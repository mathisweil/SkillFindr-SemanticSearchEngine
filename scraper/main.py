import logging
import pandas as pd
from datetime import datetime
from utils.config import load_config
from scraper.IBM_scraper import IBMScraper
from utils.selenium_utils import init_driver


def save_courses_data(courses, config):
    """
    Saves the scraped courses data to CSV and JSON files.

    Args:
        courses (list): List of dictionaries containing course information.
        config (dict): Configuration dictionary with paths and filenames.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    df = pd.DataFrame(courses)
    csv_filename = f"{config['raw_output_path']}/{config['output_filename']}_{current_date}.csv"
    json_filename = f"{config['raw_output_path']}/{config['output_filename']}_{current_date}.json"
    df.to_csv(csv_filename, index=False)
    df.to_json(json_filename, orient="records", indent=4)
    logging.info(f"Data successfully saved to CSV: {csv_filename} and JSON: {json_filename}")


def main():
    config = load_config()
    logging.basicConfig(
        filename=config["log_path"],
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    try:
        with init_driver(config) as driver:
            driver.get(config["login_url"])
            logging.info(f"Navigated to {config['login_url']}.")
            scraper = IBMScraper(driver, config)
            scraper.login()
            courses = scraper.scrape_courses()
            if not courses:
                logging.warning("No courses to process.")
            else:
                save_courses_data(courses, config)
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")


if __name__ == '__main__':
    main()
