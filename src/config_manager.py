import json
import os
from typing import List, Dict, Any

CONFIG_FILE = "docbrain_config.json"

DEFAULT_CONFIG = {
    "watch_paths": ["./data"],
    "schedule_interval_minutes": 60,
    "enable_watchdog": True,
    "enable_scheduler": True,
    "api_key": "docbrain_default_key",
    "deepseek_api_key": ""
}

class ConfigManager:
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), config_file)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_file):
            return self.save_config(DEFAULT_CONFIG)
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Ensure all default keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                return loaded_config
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return DEFAULT_CONFIG

    def save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            self.config = config
            return config
        except Exception as e:
            print(f"Error saving config: {e}")
            return self.config

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save_config(self.config)

    def update(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
        self.save_config(self.config)

config_manager = ConfigManager()
