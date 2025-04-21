import os
import json
import logging
import yaml
from typing import Any
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def load_config() -> dict[str, Any]:
    """
    Load configuration from a JSON file.

    If CONFIG_PATH is defined in the environment, it will be used.
    Otherwise, defaults to 'config.json' in the same directory as this script.

    Returns:
        dict[str, Any]: Configuration as a dictionary.

    Raises:
        SystemExit: If the file does not exist or contains invalid JSON.
    """
    load_dotenv()
    path = os.getenv("CONFIG_PATH", "config.json")
    config_path = Path(path)

    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent / config_path

    if not config_path.exists():
        logging.error("config.json not found at: %s", config_path)
        raise SystemExit(f"Error: config.json file not found at {config_path}.")

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            logging.info("Configuration successfully loaded from %s", config_path)
            return config
    except json.JSONDecodeError as e:
        logging.error("Invalid JSON in config.json: %s", e)
        raise SystemExit("Error: Invalid JSON format in config.json.")


def load_boilerplate_phrases() -> list[str]:
    """
    Load boilerplate phrases from a YAML file defined in the config.json.

    Returns:
        list[str]: List of boilerplate phrases.
    """

    path = os.getenv("BOILERPLATE_PATH", "boilerplate_phrases.yml")
    boilerplate_path = Path(path)
    if not boilerplate_path.is_absolute():
        boilerplate_path = Path(__file__).resolve().parent / boilerplate_path

    if not boilerplate_path.exists():
        raise FileNotFoundError(f"boilerplate_phrases.yml not found at: {boilerplate_path}")

    with boilerplate_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("boilerplate_phrases", [])


def get_database_engine(database_url: str) -> Engine:
    """
    Load environment variables and return an SQLAlchemy engine.

    Returns:
        sqlalchemy.Engine: Engine connected to the specified DATABASE_URL.
    """
    return create_engine(database_url)
