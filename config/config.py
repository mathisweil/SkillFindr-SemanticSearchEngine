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
    Otherwise, defaults to 'config/config.json' in the same directory as this script.

    Returns:
        dict[str, Any]: Configuration as a dictionary.

    Raises:
        SystemExit: If the file does not exist or contains invalid JSON.
    """
    load_dotenv()
    BASE_DIR = Path(__file__).resolve().parent.parent
    CONFIG_PATH = BASE_DIR / os.getenv("CONFIG_PATH", "config/config.json")

    if not CONFIG_PATH.exists():
        logging.error("config.json not found at: %s", CONFIG_PATH)
        raise SystemExit(f"Error: config.json file not found at {CONFIG_PATH}.")

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            logging.info("Configuration successfully loaded from %s", CONFIG_PATH)
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
    load_dotenv()
    BASE_DIR = Path(__file__).resolve().parent.parent
    BOILERPLATE_PATH = BASE_DIR / os.getenv("BOILERPLATE_PATH", "config/boilerplate.yaml")

    if not BOILERPLATE_PATH.exists() or not BOILERPLATE_PATH.is_file():
        return []

    with BOILERPLATE_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("boilerplate_phrases", [])


def get_database_engine(database_url: str) -> Engine:
    """
    Load environment variables and return an SQLAlchemy engine.

    Returns:
        sqlalchemy.Engine: Engine connected to the specified DATABASE_URL.
    """
    return create_engine(database_url)
