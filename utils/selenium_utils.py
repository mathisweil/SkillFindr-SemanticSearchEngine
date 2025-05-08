import logging
from typing import Any

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def init_driver(config: dict[str, Any]) -> WebDriver:
    """Initialises the Chrome WebDriver with specified options from the configuration.

    Args:
        config (dict[str, any]): Configuration dictionary containing webdriver options.

    Returns:
        WebDriver: An instance of the Chrome WebDriver.
    """
    options = webdriver.ChromeOptions()
    webdriver_args = config.get("webdriver_args", {})
    for arg in webdriver_args.values():
        options.add_argument(arg)

    logging.info("Chrome WebDriver initialised with options: %s", webdriver_args)
    return webdriver.Chrome(options=options)

def wait_for_element(
    driver: WebDriver,
    by: str,
    value: str,
    condition: any,
    timeout: int = 10
) -> WebElement | None:
    """Waits for an element to satisfy the specified condition within a given timeout.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        by (By): Locator strategy (e.g., By.ID, By.CLASS_NAME).
        value (str): The locator value (e.g., the element's ID or class name).
        condition (any): Expected condition callable (from selenium.webdriver.support.expected_conditions).
        timeout (int, optional): Maximum time to wait in seconds. Defaults to 10.

    Returns:
        WebElement | None: The WebElement if found; otherwise, None.
    """
    try:
        return WebDriverWait(driver, timeout).until(condition((by, value)))
    except TimeoutException:
        logging.warning("Element with %s='%s' not found within %d seconds.", by, value, timeout)
        return None

def wait_and_perform_action(
    driver: WebDriver,
    by: str,
    value: str,
    condition: any,
    keys: str | None = None,
    submit: bool = False
) -> None:
    """Waits for an element and performs an action such as clicking or sending keys.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        by (By): Locator strategy.
        value (str): The locator value (e.g., element's ID or class name).
        condition (any): Expected condition callable (e.g., element_to_be_clickable).
        keys (str | None, optional): Text to send to the element if provided.
        submit (bool, optional): Whether to submit the form after sending keys. Defaults to False.
    """
    element = wait_for_element(driver, by, value, condition)
    if element:
        if keys:
            element.send_keys(keys)
            if submit:
                element.submit()
        else:
            element.click()

def click_show_more_button(driver: WebDriver, delay: int) -> None:
    """Continuously clicks the 'Show More' button until it is no longer available.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
        delay (int): Time in seconds to wait after each click for the next button to appear.
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
