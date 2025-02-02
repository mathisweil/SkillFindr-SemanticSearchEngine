import time
import logging
from bs4 import BeautifulSoup
from selenium.common import TimeoutException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.utils import init_driver, clean_text
from utils.io_utils import save_to_csv, save_to_json



def extract_elements(selector, soup, single=True, unwanted_selector=None, attribute=None):
    """
    Extracts text or attribute values from elements in a BeautifulSoup object.

    :param selector: CSS selector to find the desired elements.
    :param soup: BeautifulSoup instance containing the HTML to parse.
    :param single: Determines whether to return a single element or a list of elements.
    :param unwanted_selector: CSS selector for unwanted child elements to remove before extraction.
    :param attribute: If specified, extracts the given attribute value instead of text.
    :return: Cleaned text or attribute value(s). Returns 'N/A' if no element is found.
    """
    if single:
        element = soup.select_one(selector)
        if element:
            if unwanted_selector:
                for unwanted_child in element.select(unwanted_selector):
                    unwanted_child.decompose()
            if attribute:
                return clean_text(element.get(attribute, 'N/A'))
            return clean_text(element.text)
        return "N/A"
    else:
        elements = soup.select(selector)
        if elements:
            values = []
            for elem in elements:
                if unwanted_selector:
                    for unwanted_child in elem.select(unwanted_selector):
                        unwanted_child.decompose()
                if attribute:
                    values.append(clean_text(elem.get(attribute, 'N/A')))
                else:
                    values.append(clean_text(elem.text))
            return values
        return "N/A"


def wait_for_element(driver, by, value, condition, timeout=10):
    """
        Waits for an element to meet the specified condition within a given timeout.

        :param driver: Selenium WebDriver instance.
        :param by: Locator strategy (e.g., By.ID, By.CLASS_NAME).
        :param value: The locator (e.g., the element's ID or class name).
        :param condition: The expected condition from selenium.webdriver.support.
        :param timeout: Maximum time to wait (in seconds).
        :return: The WebElement if found, otherwise None.
        """
    try:
        return WebDriverWait(driver, timeout).until(condition((by, value)))
    except TimeoutException:
        logging.warning(f"Element with {by}='{value}' not found within the given time.")
        return None


def wait_and_perform_action(driver, by, value, condition, keys=None, submit=False):
    """
    Waits for an element and performs an action (click or send_keys).

    :param driver: Selenium WebDriver instance.
    :param by: Locator strategy.
    :param value: The locator string (ID, class name, etc.).
    :param condition: Expected condition to check (e.g., element_to_be_clickable).
    :param keys: Text to send to the element if any.
    :param submit: Whether to submit the form after sending keys.
    """
    element = wait_for_element(driver, by, value, condition)
    if element:
        if keys:
            element.send_keys(keys)
            if submit:
                element.submit()
        else:
            element.click()


def click_show_more_button(driver, delay):
    """
    Continuously clicks the 'Show More' button until it no longer appears.

    :param driver: Selenium WebDriver instance.
    :param delay: Time to wait (in seconds) after each click for the next button to appear.
    """
    while True:
        show_more_button = wait_for_element(
            driver,
            By.CLASS_NAME,
            "ShowMoreButton_showMoreBtn__z194i",
            EC.element_to_be_clickable,
            timeout=delay
        )
        if show_more_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
            show_more_button.click()
            time.sleep(delay)
        else:
            break


def scrape_course_page(driver, link):
    """
    Opens a course page in a new tab, extracts course data, then closes the tab.

    :param driver: Selenium WebDriver instance.
    :param link: URL of the course page to scrape.
    :return: A dictionary containing scraped information about the course.
    """
    driver.execute_script("window.open(arguments[0]);", link)
    driver.switch_to.window(driver.window_handles[-1])

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
    soup = BeautifulSoup(html_source, 'lxml')

    course_data = {
        "type": extract_elements('#full-page-header-type', soup),
        "title": extract_elements(
            'h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span',
            soup
        ),
        "duration": extract_elements(
            '#a11y-undefined-duration, #a11y-undefined-time',
            soup,
            unwanted_selector=".sr-only"
        ),
        "learners_amount": extract_elements(
            '.LearnersAmount_learnersAmount__qttyB span[class^="ActivityFullPage_textClass__"]',
            soup
        ),
        "star_rating": extract_elements(
            '#a11y-undefined-rating', soup, attribute='title'
        ),
        "star_num_ratings": extract_elements('.Stars_numRatings__us9ns', soup),
        "description": extract_elements(
            '.FullPageDescription_wrapper__CEPjU > div', soup
        ),
        "tags": extract_elements(
            '[class^="TagLabel_labelContainer__"] > span', soup, single=False
        )
    }

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return course_data


def scraper(config):
    """
    Main scraping function that logs in, searches for courses, and extracts data.

    :param config: Dictionary containing configuration parameters (e.g. credentials, URLs).
    """
    logging.info("Scraper started.")

    with init_driver(config) as driver:
        driver.get(config["login_url"])
        logging.info(f"Navigated to {config['login_url']}.")

        # Perform login.
        try:
            wait_and_perform_action(driver, By.CSS_SELECTOR, '[btntype="ibm"]', EC.element_to_be_clickable)
            wait_and_perform_action(
                driver,
                By.ID,
                'username',
                EC.presence_of_element_located,
                keys=config["auth"]["username"],
                submit=True
            )
            wait_and_perform_action(
                driver,
                By.ID,
                'password',
                EC.presence_of_element_located,
                keys=config["auth"]["password"],
                submit=True
            )
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return

        wait_for_element(driver, By.ID, 'search-input', EC.presence_of_element_located)

        courses, scraped_courses = [], set()
        search_sections = config.get("search_sections", {})

        for section, slug in search_sections.items():
            try:
                url = f"{config["base_url"]}/search/{slug}/q={config["search_keyword"]}"
                driver.get(url)

                wait_for_element(
                    driver,
                    By.CLASS_NAME,
                    "ShowMoreButton_showMoreBtn__z194i",
                    EC.element_to_be_clickable
                )

                click_show_more_button(driver, config["scrape_delay"])

                courses_container = wait_for_element(
                    driver,
                    By.CLASS_NAME,
                    "FocusOnShowMoreWrapper_wrapper__Ord-a",
                    EC.presence_of_element_located
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
                    links = [course.get_attribute("href") for course in course_links if course.get_attribute("href")]

                    for link in links:
                        if link not in scraped_courses:
                            course_data = scrape_course_page(driver, link)
                            courses.append(course_data)
                            scraped_courses.add(link)
            except Exception as e:
                logging.error(f"Error scraping section {section}: {e}")

    output_formats = config.get("output_formats", {})

    if courses:
        if output_formats.get("csv"):
            csv_output_path = f"{config['output_path']}/{config['search_keyword']}_output"
            save_to_csv(courses, csv_output_path)
        if output_formats.get("json"):
            json_output_path = f"{config['output_path']}/{config['search_keyword']}_output"
            save_to_json(courses, json_output_path)
