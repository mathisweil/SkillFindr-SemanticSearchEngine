import logging
from selenium import webdriver


def init_driver(config):
    """Initializes the Chrome WebDriver with options."""
    options = webdriver.ChromeOptions()

    webdriver_args = config.get("webdriver_args", {})
    for webdriver_arg in webdriver_args:
        options.add_argument(webdriver_arg)

    logging.info("Chrome WebDriver initialised.")
    return webdriver.Chrome(options=options)


def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text