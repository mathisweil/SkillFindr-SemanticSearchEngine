import csv
import json
import logging


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