import json
import os
from utils.logging import get_logger

logger = get_logger(__name__)

class UserConfig:
    """
    Manages user-defined configuration settings such as risk profile.
    Loads and saves settings to a JSON file.
    """
    def __init__(self):
        self.config_file = "user_data/user_config.json"
        self._config = self._load_config_from_file()

    def _load_config_from_file(self) -> dict:
        """
        Loads configuration settings from the JSON file.
        Initializes with default values if the file doesn't exist or is invalid.
        """
        default_config = {
            "risk_profile": "Medium" # Default risk level
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    logger.info("User configuration loaded successfully.")
                    return config
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding user_config.json: {e}. Using default configuration.")
                return default_config
            except Exception as e:
                logger.error(f"Error loading user_config.json: {e}. Using default configuration.")
                return default_config
        logger.info("user_config.json not found. Creating with default configuration.")
        self._save_config(default_config) # Save defaults if file doesn't exist
        return default_config

    def _save_config(self, config_data: dict):
        """
        Saves the current configuration settings to the JSON file.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            logger.info("User configuration saved successfully.")
        except Exception as e:
            logger.error(f"Error saving user configuration to file: {e}")

    def get_risk_profile(self) -> str:
        """
        Returns the current user-defined risk profile.
        """
        return self._config.get("risk_profile", "Medium")

    def save_risk_profile(self, risk_level: str):
        """
        Saves the user's risk profile.
        Args:
            risk_level (str): 'Low', 'Medium', or 'High'.
        """
        if risk_level in ["Low", "Medium", "High"]:
            self._config["risk_profile"] = risk_level
            self._save_config(self._config)
            logger.info(f"Risk profile set to: {risk_level}")
        else:
            logger.warning(f"Invalid risk level provided: {risk_level}. Must be 'Low', 'Medium', or 'High'.")

    # Future: Add methods for other user preferences.