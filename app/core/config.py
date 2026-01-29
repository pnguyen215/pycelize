"""
Configuration Management Module

This module provides configuration loading and management functionality
using YAML files with support for nested key access.
"""

import os
import yaml
from typing import Any, Optional, Dict


class Config:
    """
    Configuration manager for loading and accessing YAML-based configuration.

    This class provides a clean interface for loading configuration from YAML files
    and accessing nested configuration values using dot notation.

    Attributes:
        _config: Internal dictionary storing configuration values
        _path: Path to the configuration file

    Example:
        >>> config = Config('configs/application.yml')
        >>> db_host = config.get('database.host', 'localhost')
        >>> api_version = config.get('api.version')
    """

    def __init__(self, config_path: str):
        """
        Initialize configuration from YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid YAML
        """
        self._path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """
        Load configuration from YAML file.

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid YAML
        """
        if not os.path.exists(self._path):
            raise FileNotFoundError(f"Configuration file not found: {self._path}")

        with open(self._path, "r", encoding="utf-8") as file:
            self._config = yaml.safe_load(file) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Supports nested key access using dot notation (e.g., 'database.host').

        Args:
            key: Configuration key using dot notation
            default: Default value if key is not found

        Returns:
            Configuration value or default if not found

        Example:
            >>> config.get('app.name', 'MyApp')
            'Pycelize'
            >>> config.get('app.debug', False)
            True
        """
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()

    def get_section(self, section: str) -> Optional[Dict[str, Any]]:
        """
        Get a complete configuration section.

        Args:
            section: Section name (top-level key)

        Returns:
            Section configuration dictionary or None if not found
        """
        return self._config.get(section)

    def reload(self) -> None:
        """
        Reload configuration from file.

        Useful for hot-reloading configuration without restarting the application.
        """
        self._load_config()

    def __repr__(self) -> str:
        """String representation of Config instance."""
        return f"Config(path='{self._path}')"
