import logging
from pathlib import Path
from typing import Any

import pandas as pd

def save_data(data: list[dict[str, Any]] | pd.DataFrame, csv_filename: Path = None, json_filename: Path = None) -> None:
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


def load_data(directory: Path) -> pd.DataFrame:
    """
    Loads all JSON files from the specified directory into a single pandas DataFrame.
    Removes duplicate entries based on the 'course_id' field.

    Parameters:
        directory (str | Path): Path to the directory containing JSON files.

    Returns:
        pd.DataFrame: Combined DataFrame of all loaded data, with duplicates removed.
    """
    dataframes = []

    for file_path in sorted(directory.glob("*.json")):
        try:
            df = pd.read_json(file_path)
            dataframes.append(df)
        except ValueError as e:
            print(f"Warning: Failed to read {file_path} — {e}")

    if not dataframes:
        return pd.DataFrame()

    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df