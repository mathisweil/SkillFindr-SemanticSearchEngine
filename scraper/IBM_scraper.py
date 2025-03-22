import logging
from contextlib import contextmanager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from typing import Dict, List

from utils.selenium_utils import wait_for_element, wait_and_perform_action, click_show_more_button
from scraper.html_parser import parse_course_page


class IBMScraper:
    def __init__(self, driver, config: Dict):
        self.driver = driver
        self.config = config

    def login(self) -> None:
        """
        Logs into the website using credentials from the configuration.
        """
        try:
            wait_and_perform_action(
                self.driver, By.CSS_SELECTOR, '[btntype="ibm"]', EC.element_to_be_clickable
            )
            wait_and_perform_action(
                self.driver,
                By.ID,
                'username',
                EC.presence_of_element_located,
                keys=self.config["auth"]["username"],
                submit=True
            )
            wait_and_perform_action(
                self.driver,
                By.ID,
                'password',
                EC.presence_of_element_located,
                keys=self.config["auth"]["password"],
                submit=True
            )
            logging.info("Login successful.")
        except Exception as e:
            logging.error(f"Login failed: {e}")
            raise

    @contextmanager
    def open_new_tab(self, url: str):
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

    def scrape_course_page(self, link: str) -> Dict:
        """
        Scrapes a single course page.

        Args:
            link (str): URL of the course page.

        Returns:
            Dict: Extracted course data.
        """
        with self.open_new_tab(link):
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
                    EC.presence_of_all_elements_located
                )
                html_source = self.driver.page_source
                course_data = parse_course_page(
                    html_source, link, self.config["course_category"]
                )
                return course_data
            except Exception as e:
                logging.error(f"Error scraping course page {link}: {e}")
                return {}

    def scrape_courses(self) -> List[Dict]:
        """
        Scrapes multiple course pages from various search sections.

        Returns:
            List[Dict]: A list of dictionaries containing course information.
        """
        wait_for_element(self.driver, By.ID, 'search-input', EC.presence_of_element_located)
        courses = []
        scraped_courses = set()
        search_sections = self.config.get("search_sections", {})

        for section, slug in search_sections.items():
            try:
                url = f"{self.config['base_url']}/search/{slug}/q={self.config['search_keyword']}"
                self.driver.get(url)
                element = WebDriverWait(self.driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, 'SearchNoResults_container__XFV7d')),
                        EC.presence_of_element_located((By.CLASS_NAME, 'FocusOnShowMoreWrapper_wrapper__Ord-a'))
                    )
                )
                if 'SearchNoResults_container__XFV7d' in element.get_attribute("class"):
                    logging.info(f"No search results for section: {section}")
                    continue

                click_show_more_button(self.driver, self.config["scrape_delay"])

                courses_container = wait_for_element(
                    self.driver,
                    By.CLASS_NAME,
                    "FocusOnShowMoreWrapper_wrapper__Ord-a",
                    EC.presence_of_element_located,
                )
                if courses_container:
                    course_links = courses_container.find_elements(
                        By.XPATH,
                        (
                            '//div[contains(@class, "overflowContainer ItemCard_overflowContainer__tpWp9")]'
                            '/div[contains(@class, "ItemCard_itemCardContainer__EJsD7")]'
                            '/a[contains(@class, "ItemCard_linkContainer__jUUXI")]'
                        )
                    )
                    links = [
                        course.get_attribute("href")
                        for course in course_links if course.get_attribute("href")
                    ]
                    for link in links:
                        if link not in scraped_courses:
                            course_data = self.scrape_course_page(link)
                            if course_data:
                                courses.append(course_data)
                            scraped_courses.add(link)
            except Exception as e:
                logging.error(f"Error scraping section {section}: {e}")
        return courses
