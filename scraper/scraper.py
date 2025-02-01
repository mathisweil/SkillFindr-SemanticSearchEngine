import time
import logging
from bs4 import BeautifulSoup
from selenium.common import TimeoutException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import load_config, setup_logger, init_driver, save_to_csv, save_to_json


def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text

def extract_elements(selector, soup, single=True, unwanted_selector=None, attribute=None):
    if single:
        element = soup.select_one(selector)
        if element:
            if unwanted_selector:
                for unwanted_child in element.select(unwanted_selector):
                    unwanted_child.decompose()
            return clean_text(element[attribute]) if attribute else clean_text(element.text)
        return "N/A"
    else:
        elements = soup.select(selector)
        if elements:
            fields = []
            for element in elements:
                if unwanted_selector:
                    for unwanted_child in element.select(unwanted_selector):
                        unwanted_child.decompose()
                fields.append(clean_text(element.text))
            return fields
        return "N/A"


def wait_for_element(driver, by, value, condition, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(condition((by, value)))
    except TimeoutException:
        logging.warning(f"Element with {by}='{value}' not found within the given time.")
        return None


def wait_and_interact(driver, by, value, interaction, keys=None, submit=False):
    element = wait_for_element(driver, by, value, interaction)
    if element:
        if keys:
            element.send_keys(keys)
            if submit:
                element.submit()
        else:
            element.click()


def handle_show_more_button(driver, delay):
    """Click 'Show More' button until no more buttons are found."""
    while True:
        wait_for_element(driver, By.CLASS_NAME, "ShowMoreButton_showMoreBtn__z194i", EC.element_to_be_clickable)
        buttons = driver.find_elements(By.CLASS_NAME, "ShowMoreButton_showMoreBtn__z194i")
        if buttons:
            show_more_button = buttons[0]
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
            show_more_button.click()
            time.sleep(delay)
        else:
            break


def scrape_course_page(driver, link, config):
    """Scrape individual course page."""
    driver.execute_script("window.open(arguments[0]);", link)
    driver.switch_to.window(driver.window_handles[-1])

    wait_for_element(driver, By.CSS_SELECTOR, 'div[class*="FullPageDescription_wrapper__CEPjU"] > div', EC.presence_of_element_located)
    wait_for_element(driver, By.CSS_SELECTOR, '[class^="TagLabel_labelContainer__"] > span', EC.presence_of_all_elements_located)

    # Get page source and parse with BeautifulSoup
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'lxml')

    # Extract course data
    course_data = {
        "type": extract_elements('#full-page-header-type', soup),
        "title": extract_elements('h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span', soup),
        "duration": extract_elements('#a11y-undefined-duration, #a11y-undefined-time', soup, unwanted_selector=".sr-only"),
        "learners_amount": extract_elements('.LearnersAmount_learnersAmount__qttyB span[class^="ActivityFullPage_textClass__"]', soup),
        "star_rating": extract_elements('#a11y-undefined-rating', soup, attribute='title'),
        "star_num_ratings": extract_elements('.Stars_numRatings__us9ns', soup),
        "description": extract_elements('.FullPageDescription_wrapper__CEPjU > div', soup),
        "tags": extract_elements('[class^="TagLabel_labelContainer__"] > span', soup, single=False)
    }

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return course_data


def scraper(config):
    logging.info("Scraper started.")

    with init_driver(config) as driver:
        driver.get(config["login_url"])
        logging.info(f"Navigated to {config['login_url']}.")

        wait_and_interact(driver, By.CSS_SELECTOR, '[btntype="ibm"]', EC.element_to_be_clickable)
        wait_and_interact(driver, By.ID, 'username', EC.presence_of_element_located, config["auth"]["username"],
                          submit=True)
        wait_and_interact(driver, By.ID, 'password', EC.presence_of_element_located, config["auth"]["password"],
                          submit=True)

        wait_for_element(driver, By.ID, 'search-input', EC.presence_of_element_located)

        courses = []
        search_sections = config.get("search_sections", {})
        for section, slug in search_sections.items():
            url = f"{config["base_url"]}/search/{slug}/q={config["search_keyword"]}"
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ShowMoreButton_showMoreBtn__z194i"))
            )

            handle_show_more_button(driver, config["scrape_delay"])


            courses_container = driver.find_element(By.CLASS_NAME, "FocusOnShowMoreWrapper_wrapper__Ord-a")
            courses = courses_container.find_elements(By.XPATH,
                                                      '//div[contains(@class, "overflowContainer ItemCard_overflowContainer__tpWp9")]/div[contains(@class, "ItemCard_itemCardContainer__EJsD7")]/a[contains(@class, "ItemCard_linkContainer__jUUXI")]')

            links = [course.get_attribute("href") for course in courses if course.get_attribute("href")]

            for link in links:
                course_data = scrape_course_page(driver, link, config)
                driver.switch_to.window(driver.window_handles[0])

    output_formats = config.get("output_formats", {})
    if output_formats.get("csv"):
        save_to_csv(courses, config.get["output_path"])
    if output_formats.get("json"):
        save_to_json(courses, config.get["output_path"])


if __name__ == '__main__':
    config_file = load_config()
    setup_logger(config_file)
    scraper(config_file)
