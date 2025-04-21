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
    Load configuration from config/config.json at the project root.

    Returns:
        dict[str, Any]: A dictionary containing configuration settings.

    Raises:
        SystemExit: If the config file is missing or invalid.
    """
    try:
        base_path = Path(__file__).resolve().parent.parent
        config_path = base_path / "config" / "config.json"

        with config_path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            logging.info("Configuration successfully loaded from %s", config_path)
            return config

    except FileNotFoundError:
        logging.error("config.json not found at: %s", config_path)
        raise SystemExit("Error: config.json file not found.")
    except json.JSONDecodeError as e:
        logging.error("Invalid JSON in config.json: %s", e)
        raise SystemExit("Error: Invalid JSON format in config.json.")


def get_database_engine() -> Engine:
    """
    Load environment variables and return an SQLAlchemy engine.

    Returns:
        sqlalchemy.Engine: Engine connected to the specified DATABASE_URL.
    """
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set in environment variables.")
    return create_engine(database_url)


def load_boilerplate_phrases(config: dict[str, Any] | None = None) -> list[str]:
    """
    Load boilerplate phrases from a YAML file defined in the config.json.

    Args:
        config (dict[str, Any], optional): Loaded project config. If None, it is loaded automatically.

    Returns:
        list[str]: List of boilerplate phrases.
    """
    if config is None:
        config = load_config()

    path = config.get("boilerplate_phrases_path", "config/boilerplate_phrases.yml")
    boilerplate_path = Path(path)
    if not boilerplate_path.is_absolute():
        boilerplate_path = Path(__file__).resolve().parent.parent / boilerplate_path

    if not boilerplate_path.exists():
        raise FileNotFoundError(f"boilerplate_phrases.yml not found at: {boilerplate_path}")

    with boilerplate_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("boilerplate_phrases", [])
