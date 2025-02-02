import logging
from selenium import webdriver


def init_driver(config):
    """Initializes the Chrome WebDriver with options."""
    options = webdriver.ChromeOptions()

    webdriver_args = config.get("webdriver_args", {})
    if webdriver_args.get("headless"):
        options.add_argument("--headless")

    logging.info("Chrome WebDriver initialised.")
    return webdriver.Chrome(options=options)


def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text