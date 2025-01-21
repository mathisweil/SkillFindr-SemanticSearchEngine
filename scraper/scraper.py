import time
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import load_config, setup_logger, init_driver

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
        time.sleep(10)

        search_sections = config.get("search_sections", {})
        for section, slug in search_sections.items():
            url = f"{config["base_url"]}/search/{slug}/q={config["search_keyword"]}"
            driver.get(url)
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

            courses = driver.find_elements(By.XPATH, '//div[contains(@class, "FocusOnShowMoreWrapper_wrapper__Ord-a")]/div[contains(@class, "overflowContainer ItemCard_overflowContainer__tpWp9")]')
            links = [course.get_attribute("href") for course in courses]
            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[-1])

        time.sleep(config["scrape_delay"])


if __name__ == '__main__':
    config_file = load_config()
    setup_logger(config_file)
    scraper(config_file)