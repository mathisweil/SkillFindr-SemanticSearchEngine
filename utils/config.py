import os
import json


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