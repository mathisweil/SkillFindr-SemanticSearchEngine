import json
import csv
import logging
import os
from selenium import webdriver


def load_config():
    """Loads the configuration from the config.json file."""
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, "config.json")

        with open(config_path, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print("Error: config.json file not found.")
        exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in config.json.")
        exit(1)


def setup_logger(config):
    """Sets up the logger for the scraper."""
    log_path = config.get("log_path", "./logs/scraper.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)  # Ensure the logs directory exists

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Logger initialised.")


def init_driver(config):
    """Initializes the Chrome WebDriver with options."""
    options = webdriver.ChromeOptions()

    webdriver_args = config.get("webdriver_args", {})
    if webdriver_args.get("headless"):
        options.add_argument("--headless")

    logging.info("Chrome WebDriver initialised.")
    return webdriver.Chrome(options=options)


def save_to_csv(data, file_name):
    """
    Saves the given list of dictionaries to a CSV file.

    :param data: A list of dictionaries containing the data to be saved.
    :param file_name: The name of the output file without extension.
    """
    try:
        with open(f'{file_name}.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Data successfully saved to {file_name}.csv")

    except Exception as e:
        logging.error(f"Error saving data to {file_name}.csv: {e}")



def save_to_json(data, file_name):
    """
    Saves the given data to a JSON file.

    :param data: The data to be saved in JSON format.
    :param file_name: The name of the output file without extension.
    """
    try:
        with open(f'{file_name}.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        logging.info(f"Data successfully saved to {file_name}.json")
    except Exception as e:
        logging.error(f"Failed to save data to JSON: {e}")


def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text