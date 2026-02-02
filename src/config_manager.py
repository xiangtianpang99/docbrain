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
    # Legacy field - kept for backward compatibility but deprecated
    "deepseek_api_key": "",
    # New Provider Configuration
    "active_provider": "deepseek",
    "llm_providers": {
        "deepseek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "openai": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4"
        },
        "ollama": {
            "api_key": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3"
        },
        "custom": {
            "api_key": "",
            "base_url": "",
            "model": ""
        }
    }
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
                
                modified = False
                
                # 1. Ensure all default keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                        modified = True
                
                # 2. Deep merge llm_providers to ensure new providers appear
                if "llm_providers" not in loaded_config:
                     loaded_config["llm_providers"] = DEFAULT_CONFIG["llm_providers"]
                     modified = True
                else:
                    for prov, default_settings in DEFAULT_CONFIG["llm_providers"].items():
                        if prov not in loaded_config["llm_providers"]:
                             loaded_config["llm_providers"][prov] = default_settings
                             modified = True

                # 3. Backward Compatibility Migration
                # If deepseek_api_key exists in root but not in provider config, migrate it
                legacy_key = loaded_config.get("deepseek_api_key")
                provider_key = loaded_config["llm_providers"]["deepseek"]["api_key"]
                
                if legacy_key and not provider_key:
                    print("Migrating legacy DEEPSEEK_API_KEY to provider config...")
                    loaded_config["llm_providers"]["deepseek"]["api_key"] = legacy_key
                    # We don't remove the legacy key to avoid breaking other tools reading .env directly immediately
                    modified = True

                if modified:
                    print("Config updated with new defaults/migrations. Saving...")
                    self.save_config(loaded_config)
                    
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
