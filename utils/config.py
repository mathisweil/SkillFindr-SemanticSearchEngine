import os
import json
import logging


def load_config() -> dict[str, any]:
    """Load configuration from the config.json file located at the project root.

    Returns:
        dict[str, Any]: A dictionary containing configuration settings.

    Raises:
        SystemExit: If the config.json file is not found or contains invalid JSON.
    """
    global config_path
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, "config.json")

        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            logging.info("Configuration successfully loaded from %s.", config_path)
            return config
    except FileNotFoundError:
        logging.error("Error: config.json file not found at expected location: %s.", config_path)
        raise SystemExit("Error: config.json file not found.")
    except json.JSONDecodeError as e:
        logging.error("Error: Invalid JSON format in config.json: %s", e)
        raise SystemExit("Error: Invalid JSON format in config.json.")
