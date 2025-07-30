"""
Configuration management for ShellAI.

This module handles loading and managing configuration from config.yaml
and provides default values for all settings.
"""

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML not installed.")
    print("Run: pip install pyyaml")
    import sys

    sys.exit(1)


class ShellAIConfig:
    """Configuration manager for ShellAI."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_path = Path(config_path) if config_path else Path("config.yaml")
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "ollama": {
                "base_url": "http://localhost:11434",
                "default_model": "gemma2:2b",
                "request_timeout": 60.0,
            },
            "embedding": {"model": "local:BAAI/bge-small-en"},
            "system_info": {"output_dir": "system_info", "storage_dir": "storage"},
        }

    def _load_config(self) -> None:
        """Load configuration from file or create default."""
        # Start with defaults
        self._config = self._get_default_config()

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f) or {}
                # Merge user config with defaults
                self._merge_config(self._config, user_config)
            except Exception as e:
                print(f"⚠️ Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration.")
        else:
            # Create default config file
            self.create_default_config()

    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> None:
        """Recursively merge user config into default config."""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value

    def create_default_config(self) -> None:
        """Create a default configuration file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            print(f"📝 Created default configuration file: {self.config_path}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to create config file: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'ollama.base_url')."""
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key_path.split(".")
        config = self._config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the final value
        config[keys[-1]] = value

    def save(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Failed to save config: {e}")
            return False

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    @property
    def ollama_base_url(self) -> str:
        """Get Ollama base URL."""
        return self.get("ollama.base_url", "http://localhost:11434")

    @property
    def default_model(self) -> str:
        """Get default Ollama model."""
        return self.get("ollama.default_model", "mistral")

    @property
    def embedding_model(self) -> str:
        """Get embedding model."""
        return self.get("embedding.model", "local:BAAI/bge-small-en")

    @property
    def system_info_dir(self) -> str:
        """Get system info directory."""
        return self.get("system_info.output_dir", "system_info")

    @property
    def storage_dir(self) -> str:
        """Get storage directory name."""
        return self.get("system_info.storage_dir", "storage")


# Global config instance
_config: Optional[ShellAIConfig] = None


def get_config(config_path: Optional[str] = None) -> ShellAIConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None or config_path:
        _config = ShellAIConfig(config_path)
    return _config


def reload_config() -> None:
    """Reload the global configuration."""
    global _config
    if _config:
        _config.reload()
