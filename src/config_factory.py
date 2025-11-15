"""
Configuration factory for creating Config instances.

This module provides a simple factory function to create Config instances
with default parameters.
"""

from .config import Config


def create_config(config_path: str = "config.yaml") -> Config:
    """Create a configuration instance.

    Args:
        config_path: Path to the configuration file. Defaults to "config.yaml"

    Returns:
        Config: A new Config instance
    """
    return Config(config_path=config_path)