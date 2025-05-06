import logging
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from config.config import load_config
from scraper.html_parser import parse_course_page
from utils.io_utils import save_data
from utils.selenium_utils import (
    click_show_more_button,
    init_driver,
    wait_and_perform_action,
    wait_for_element,
)


class IBMScraper:
    def __init__(self, driver, config: dict):
        self.driver = driver
        self.config = config
        self.scraped_courses: set[str] = set()

    def login(self) -> None:
        """
        Logs into the website using credentials from the configuration.
        """
        try:
            login_url = os.getenv("LOGIN_URL")
            self.driver.get(login_url)
            logging.info(f"Navigated to {login_url}.")

            wait_and_perform_action(
                self.driver, By.CSS_SELECTOR, '[btntype="ibm"]', EC.element_to_be_clickable
            )
            wait_and_perform_action(
                self.driver,
                By.ID,
                'username',
                EC.presence_of_element_located,
                keys=os.getenv("USERNAME"),
                submit=True
            )
            wait_and_perform_action(
                self.driver,
                By.ID,
                'password',
                EC.presence_of_element_located,
                keys=os.getenv("PASSWORD"),
                submit=True
            )
            logging.info("Login successful.")
        except Exception as e:
            logging.error(f"Login failed: {e}")
            raise

    @contextmanager
    def __open_new_tab(self, url: str):
        """
        Context manager to open a new tab, switch to it, and ensure it is closed.

        Args:
            url (str): The URL to open in the new tab.
        """
        original_handle = self.driver.current_window_handle
        self.driver.execute_script("window.open(arguments[0]);", url)
        new_handle = self.driver.window_handles[-1]
        self.driver.switch_to.window(new_handle)
        try:
            yield
        finally:
            self.driver.close()
            self.driver.switch_to.window(original_handle)

    def __scrape_course_page(self, link: str, category: str) -> dict[str, Any]:
        """
        Scrapes a single course page.

        Args:
            link (str): URL of the course page.

        Returns:
            dict: Extracted course data.
            :param category:
        """
        with self.__open_new_tab(link):
            try:
                wait_for_element(
                    self.driver,
                    By.CSS_SELECTOR,
                    'div[class*="FullPageDescription_wrapper__CEPjU"] > div',
                    EC.presence_of_element_located
                )
                wait_for_element(
                    self.driver,
                    By.CSS_SELECTOR,
                    '[class^="TagLabel_labelContainer__"] > span',
                    EC.presence_of_all_elements_located,
                    timeout = int(os.getenv("SCRAPE_DELAY", "2"))
                )
                html_source = self.driver.page_source
                course_data = parse_course_page(
                    html_source, link, category
                )
                return course_data if course_data is not None else {}
            except Exception as e:
                logging.error(f"Error scraping course page {link}: {e}")
                return {}

    @staticmethod
    def __parse_course_links(container: Any) -> list[str]:
        """
        Given a container element (sponsored or normal), finds
        and returns all relevant course hrefs.
        """
        links: list[str] = []
        try:
            course_cards = container.find_elements(
                By.XPATH,
                './/div[contains(@class, "overflowContainer ItemCard_overflowContainer__tpWp9")]'
            )
            for card in course_cards:
                try:
                    link_element = card.find_element(
                        By.XPATH,
                        './div[contains(@class, "ItemCard_itemCardContainer__EJsD7")]/a[contains(@class, "ItemCard_linkContainer__jUUXI")]'
                    )
                    href = link_element.get_attribute("href")
                    if href:
                        links.append(href)
                except Exception as e:
                    logging.debug(f"Failed to extract link from card: {e}")
                    continue
        except Exception as e:
            logging.error(f"Error parsing course links: {e}")
        return links

    def scrape_courses(self, search_category: str) -> list[dict[str, Any]]:
        """
        Scrapes multiple course pages from various search sections.

        Returns:
            list[dict]: A list of dictionaries containing course information.
        """
        courses: list[dict[str, Any]] = []
        try:
            wait_for_element(self.driver, By.ID, 'search-input', EC.presence_of_element_located)

            search_sections = self.config.get("search_sections", {})
            for section, slug in search_sections.items():
                try:
                    keyword = search_category.replace("_", "%20")
                    language_filters = self.config.get("language_filters", {})
                    language_query = "&".join([f"languages={lang}" for lang in language_filters.values()])
                    base_url = os.getenv("BASE_URL")
                    url = f"{base_url}/search/{slug}/q={keyword}&{language_query}"
                    self.driver.get(url)
                    logging.info(f"Navigated to {url}.")

                    element = WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, 'SearchNoResults_container__XFV7d')),
                            EC.presence_of_element_located((By.CLASS_NAME, 'FocusOnShowMoreWrapper_wrapper__Ord-a'))
                        )
                    )
                    if 'SearchNoResults_container__XFV7d' in element.get_attribute("class"):
                        logging.info(f"No search results for section: {section}")
                        continue

                    click_show_more_button(self.driver, int(os.getenv("SCRAPE_DELAY", "2")))

                    links: list[str] = []
                    try:
                        container = self.driver.find_element(
                            By.CLASS_NAME,
                            "withSearch_resultsContainer__msvVY"
                        )
                        links = self.__parse_course_links(container)
                        logging.info(f"Found {len(links)} links for section: {section}")
                    except Exception:
                        logging.info("No results container found.")

                    for link in links:
                        if link not in self.scraped_courses:
                            course_data = self.__scrape_course_page(link, search_category)
                            if course_data:
                                courses.append(course_data)
                            self.scraped_courses.add(link)
                except Exception as e:
                    logging.error(f"Error scraping section {section}: {e}")
        except Exception as e:
            logging.error(f"Failed scraping for keyword {search_category}: {e}")
        return courses


def main():
    load_dotenv()
    config = load_config()

    BASE_DIR = Path(__file__).resolve().parent.parent

    log_path_raw = os.getenv("LOG_PATH", "logs/ibm_scraper.log")
    log_path_full = BASE_DIR / log_path_raw

    log_path_full.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=log_path_full,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    try:
        RAW_OUTPUT_PATH = BASE_DIR / os.getenv("RAW_OUTPUT_PATH", "output/raw_data")
        RAW_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

        with init_driver(config) as driver:
            scraper = IBMScraper(driver, config)
            scraper.login()

            search_categories = config.get("search_categories", {})

            for search_category in search_categories:
                courses = scraper.scrape_courses(search_category)
                if not courses:
                    logging.warning(f"No courses to process for: {search_category}.")
                else:
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    csv_filename = RAW_OUTPUT_PATH / f"{search_category}_{current_date}.csv"
                    json_filename = RAW_OUTPUT_PATH / f"{search_category}_{current_date}.json"

                    save_data(courses, csv_filename, json_filename)
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")


if __name__ == '__main__':
    main()
