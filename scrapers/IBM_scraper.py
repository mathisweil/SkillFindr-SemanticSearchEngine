import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_utils import wait_for_element, wait_and_perform_action, click_show_more_button
from parsers.course_parser import parse_course_page

class IBMScraper:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config


    def login(self):
        try:
            wait_and_perform_action(self.driver, By.CSS_SELECTOR, '[btntype="ibm"]', EC.element_to_be_clickable)
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
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return

    def scrape_course_page(self, link):
        """
        Opens a course page in a new tab, extracts course data, then closes the tab.

        :param link: URL of the course page to scrape.
        :return: A dictionary containing scraped information about the course.
        """
        self.driver.execute_script("window.open(arguments[0]);", link)
        self.driver.switch_to.window(self.driver.window_handles[-1])

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
        course_data = parse_course_page(html_source)

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return course_data


    def scrape_courses(self):
        wait_for_element(self.driver, By.ID, 'search-input', EC.presence_of_element_located)

        courses, scraped_courses = [], set()
        search_sections = self.config.get("search_sections", {})

        for section, slug in search_sections.items():
            try:
                url = f"{self.config['base_url']}/search/{slug}/q={self.config['search_keyword']}"
                self.driver.get(url)

                wait_for_element(
                    self.driver,
                    By.CLASS_NAME,
                    "ShowMoreButton_showMoreBtn__z194i",
                    EC.element_to_be_clickable
                )

                click_show_more_button(self.driver, self.config["scrape_delay"])

                if courses_container := wait_for_element(
                        self.driver,
                        By.CLASS_NAME,
                        "FocusOnShowMoreWrapper_wrapper__Ord-a",
                        EC.presence_of_element_located,
                ):
                    course_links = courses_container.find_elements(
                        By.XPATH,
                        (
                            '//div[contains(@class, "overflowContainer ItemCard_overflowContainer__tpWp9")]'
                            '/div[contains(@class, "ItemCard_itemCardContainer__EJsD7")]'
                            '/a[contains(@class, "ItemCard_linkContainer__jUUXI")]'
                        )
                    )
                    links = [course.get_attribute("href") for course in course_links if course.get_attribute("href")]

                    for link in links:
                        if link not in scraped_courses:
                            course_data = self.scrape_course_page(link)
                            courses.append(course_data)
                            scraped_courses.add(link)
            except Exception as e:
                logging.error(f"Error scraping section {section}: {e}")
        return courses
