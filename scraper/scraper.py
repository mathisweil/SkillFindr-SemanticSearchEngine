import time
import logging
from bs4 import BeautifulSoup

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import load_config, setup_logger, init_driver


def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text

def extract_field(selector, soup, unwanted_selector=None):
    element = soup.select_one(selector)
    if element:
        if unwanted_selector:
            for unwanted_child in element.select(unwanted_selector):
                unwanted_child.decompose()

        return clean_text(element.text)
    return "N/A"


def scraper(config):
    logging.info("Scraper started.")

    with init_driver(config) as driver:
        driver.get(config["login_url"])
        logging.info(f"Navigated to {config['login_url']}.")

        ibm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[btntype="ibm"]'))
        )
        ibm_button.click()

        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        username_field.send_keys(config["auth"]["username"])
        username_field.submit()

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'password'))
        )
        password_field.send_keys(config["auth"]["password"])
        password_field.submit()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search-input'))
        )

        search_sections = config.get("search_sections", {})
        for section, slug in search_sections.items():
            url = f"{config["base_url"]}/search/{slug}/q={config["search_keyword"]}"
            driver.get(url)

            # change, what if no show more button ?
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ShowMoreButton_showMoreBtn__z194i"))
            )

            while True:
                buttons = driver.find_elements(By.CLASS_NAME, "ShowMoreButton_showMoreBtn__z194i")
                if len(buttons) > 0:
                    show_more_button = buttons[0]

                    driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)

                    show_more_button.click()

                    time.sleep(config["scrape_delay"])
                else:
                    break

            courses_container = driver.find_element(By.CLASS_NAME, "FocusOnShowMoreWrapper_wrapper__Ord-a")

            courses = courses_container.find_elements(By.XPATH,
                                                      '//div[contains(@class, "overflowContainer ItemCard_overflowContainer__tpWp9")]/div[contains(@class, "ItemCard_itemCardContainer__EJsD7")]/a[contains(@class, "ItemCard_linkContainer__jUUXI")]')

            links = [course.get_attribute("href") for course in courses if course.get_attribute("href")]

            for link in links:
                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[-1])
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                                                    'div[class*="FullPageDescription_wrapper__CEPjU"] > div'))
                )

                html_source = driver.page_source  # Get the full HTML source of the page
                soup = BeautifulSoup(html_source, 'lxml')

                # Cleaning the extracted data
                course_data = {
                    "type": extract_field('#full-page-header-type', soup),

                    "title": extract_field('h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span', soup),

                    "duration": extract_field('#a11y-undefined-duration, #a11y-undefined-time', soup, "sr-only"),

                    "learners_amount": extract_field('.LearnersAmount_learnersAmount__qttyB span[class^="ActivityFullPage_textClass__"]', soup),

                    # "star_rating": extract_field('#a11y-undefined-rating', soup),

                    "description": extract_field('.FullPageDescription_wrapper__CEPjU > div', soup)
                }
                print(course_data)
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        time.sleep(config["scrape_delay"])


if __name__ == '__main__':
    config_file = load_config()
    setup_logger(config_file)
    scraper(config_file)
