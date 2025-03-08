import json
import os

DEFAULT_CONFIG = {"directories": [os.path.expanduser("~")], "browser": "Chrome", "log_destination": "log/activity.log"}


def load_config(config_file="config.json"):
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config.update(json.load(f))
    # Ensure log_destination is local
    config["log_destination"] = "log/activity.log"
    return config
