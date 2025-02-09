import logging

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def init_driver(config):
    """Initializes the Chrome WebDriver with options."""
    options = webdriver.ChromeOptions()

    webdriver_args = config.get("webdriver_args", {})
    for webdriver_arg in webdriver_args:
        options.add_argument(webdriver_arg)

    logging.info("Chrome WebDriver initialised.")
    return webdriver.Chrome(options=options)


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
    if element := wait_for_element(driver, by, value, condition):
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
        else:
            break