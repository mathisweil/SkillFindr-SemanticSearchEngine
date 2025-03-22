import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.selenium_utils import wait_for_element, wait_and_perform_action, click_show_more_button, init_driver
from scraper.html_parser import parse_course_page


class IBMScraper:
    def __init__(self, driver, config: Dict[str, Any]):
        self.driver = driver
        self.config = config

    def login(self) -> None:
        """
        Log into the website using credentials from the configuration.
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
    def open_new_tab(self, url: str, driver) -> None:
        """
        Context manager to open a new tab, switch to it, and ensure it is closed.

        Args:
            url: The URL to open in the new tab.
            driver: Selenium WebDriver instance.
        """
        original_handle = driver.current_window_handle
        driver.execute_script("window.open(arguments[0]);", url)
        new_handle = driver.window_handles[-1]
        driver.switch_to.window(new_handle)
        try:
            yield
        finally:
            driver.close()
            driver.switch_to.window(original_handle)

    def scrape_course_page(self, link: str, driver_pool: Queue) -> Dict[str, Any]:
        """
        Scrape a single course page.

        Args:
            link: URL of the course page.
            driver_pool: Queue containing Selenium WebDriver instances.

        Returns:
            Extracted course data as a dictionary.
        """
        driver = driver_pool.get()
        try:
            with self.open_new_tab(link, driver):
                wait_for_element(
                    driver,
                    By.CSS_SELECTOR,
                    'div[class*="FullPageDescription_wrapper__CEPjU"] > div',
                    EC.presence_of_element_located
                )
                wait_for_element(
                    driver,
                    By.CSS_SELECTOR,
                    '[class^="TagLabel_labelContainer__"] > span',
                    EC.presence_of_all_elements_located
                )
                html_source = driver.page_source
                course_data = parse_course_page(
                    html_source, link, self.config["course_category"]
                )
                return course_data
        except Exception as e:
            logging.error(f"Error scraping course page {link}: {e}")
            return {}
        finally:
            driver_pool.put(driver)

    def _init_driver_pool(self, num_drivers: int) -> Queue:
        """
        Initialise a pool of Selenium WebDriver instances.

        Args:
            num_drivers: The number of drivers to initialise.

        Returns:
            A Queue containing the initialised driver instances.
        """
        cookies = self.driver.get_cookies()

        driver_pool: Queue = Queue(maxsize=num_drivers)
        for _ in range(num_drivers):
            new_driver = init_driver(self.config)
            for domain in ["ibm.com", "yourlearning.ibm.com", "skills.yourlearning.ibm.com"]:
                new_driver.get(f"https://{domain}/")  # Must load page first
                time.sleep(2)
            for cookie in cookies:
                new_driver.add_cookie(cookie)

            new_driver.refresh()

            driver_pool.put(new_driver)
        return driver_pool

    def _shutdown_driver_pool(self, driver_pool: Queue) -> None:
        """
        Gracefully shutdown all drivers in the pool.

        Args:
            driver_pool: Queue containing Selenium WebDriver instances.
        """
        while not driver_pool.empty():
            driver = driver_pool.get()
            driver.quit()

    def scrape_courses(self, max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape multiple course pages from various search sections.

        Args:
            max_workers: Maximum number of concurrent workers for scraping.

        Returns:
            A list of dictionaries containing course information.
        """

        try:
            wait_for_element(
                self.driver, By.ID, 'search-input', EC.presence_of_element_located
            )
            courses: List[Dict[str, Any]] = []
            search_sections = self.config.get("search_sections", {})

            num_drivers = 7
            driver_pool = self._init_driver_pool(num_drivers)

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
                    element_class = element.get_attribute("class") or ""
                    if 'SearchNoResults_container__XFV7d' in element_class:
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

                        with ThreadPoolExecutor(max_workers=max_workers) as executor:
                            future_to_link = {
                                executor.submit(self.scrape_course_page, link, driver_pool): link
                                for link in links
                            }
                            for future in as_completed(future_to_link):
                                link = future_to_link[future]
                                try:
                                    data = future.result()
                                    if data:
                                        courses.append(data)
                                except Exception as exc:
                                    logging.error(f"Scraping failed for {link}: {exc}")
                except Exception as e:
                    logging.error(f"Error scraping section {section}: {e}")
            return courses
        finally:
            self._shutdown_driver_pool(driver_pool)
