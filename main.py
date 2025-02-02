from utils.config import load_config
from utils.logging import setup_logger
from scrapers.scraper import scraper


if __name__ == '__main__':
    config_file = load_config()
    setup_logger(config_file)
    scraper(config_file)