
import os
import yaml
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and manage configuration settings from YAML files."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config loader.

        Args:
            config_path: Path to the YAML configuration file. If None, uses default.
        """
        if config_path is None:
            # Get the project root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, "../.."))
            config_path = os.path.join(project_root, "config", "settings.yaml")

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)
            self._validate_config(config)
            return config
        except (FileNotFoundError, yaml.YAMLError) as e:
            # Fall back to default configuration if file not found or invalid
            print(f"Warning: Failed to load config from {self.config_path}: {e}")
            print("Using default configuration.")
            return self._get_default_config()

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration structure and values.

        Raises:
            ValueError: If required sections are missing or values are invalid.
        """
        if config is None:
            raise ValueError("Config is empty or invalid YAML")

        required_sections = ["paths", "image", "logging"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required config section: '{section}'")

        # Validate image section
        image_cfg = config.get("image", {})
        dpi = image_cfg.get("default_dpi", 300)
        if not isinstance(dpi, int) or not (72 <= dpi <= 1200):
            raise ValueError(f"Invalid default_dpi: {dpi}. Must be between 72 and 1200.")

        parts = image_cfg.get("default_parts", 3)
        if not isinstance(parts, int) or parts < 1 or parts > 100:
            raise ValueError(f"Invalid default_parts: {parts}. Must be between 1 and 100.")

        # Validate A4 dimensions if present
        a4 = image_cfg.get("a4", {})
        if a4:
            for key in ["width_inches", "height_inches"]:
                val = a4.get(key)
                if val is not None and (not isinstance(val, (int, float)) or val <= 0):
                    raise ValueError(f"Invalid a4.{key}: {val}. Must be a positive number.")

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Provide default configuration in case the config file is unavailable."""
        return {
            "paths": {
                "base_output_dir": "data/image/output",
                "input_dir": "data/image/input"
            },
            "image": {
                "default_dpi": 300,
                "default_parts": 3,
                "default_format": "",
                "resampling_method": "LANCZOS",
                "a4": {
                    "width_inches": 8.27,
                    "height_inches": 11.69,
                    "width_mm": 210,
                    "height_mm": 297
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S",
                "file": "poster_maker.log"
            }
        }

    def get_config(self) -> Dict[str, Any]:
        """Return the loaded configuration."""
        return self.config