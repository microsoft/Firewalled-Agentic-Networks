from os.path import dirname, join as pathjoin
from typing import Dict, List
import yaml
import logging
import sys


def load_config(file_name: str = "config.yaml") -> Dict:
    try:
        config_path = file_name
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)  # Load the YAML file contents into a dictionary
        return config
    except FileNotFoundError:
        logging.error("Configuration file not found.", exc_info=True)
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML configuration: {e}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Unexpected error loading configuration: {e}", exc_info=True)
        raise


class Logger:
    def __init__(self, filename):
        self.log = open(filename, "w", encoding="utf-8")
        self.terminal = sys.stdout

    def write(self, message):
        self.log.write(message)
        self.terminal.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()


def log_conversations(long_answer, short_answer, from_, to_):
    return {
        "long_answer": long_answer,
        "short_answer": short_answer,
        "from": from_,
        "to": to_,
    }
