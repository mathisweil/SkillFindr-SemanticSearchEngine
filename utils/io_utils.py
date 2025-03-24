import logging
import pandas as pd

def save_data(data: list[dict[str, any]] | pd.DataFrame, csv_filename: str = None, json_filename: str = None) -> None:
    """
    Saves the data to CSV and JSON files.

    Args:
        data (list): List of dictionaries containing data.
        :param data:
        :param csv_filename:
        :param json_filename:
    """
    if data is not pd.DataFrame:
        data = pd.DataFrame(data)

    if csv_filename is not None:
        data.to_csv(csv_filename, index=False)
        logging.info(f"Data successfully saved to CSV: {csv_filename}")

    if json_filename is not None:
        data.to_json(json_filename, orient="records", indent=4)
        logging.info(f"Data successfully saved to JSON: {json_filename}")