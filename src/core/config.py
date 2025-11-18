"""Centralized configuration settings for the application.

This module provides a centralized configuration system using Pydantic Settings.
It loads configuration values from environment variables or a .env file and
exposes a single settings instance that can be imported throughout the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.

    This class defines all configurable parameters for the application.
    Settings can be overridden by environment variables or values in a .env file.

    Attributes:
        inventory_file (str): Path to the inventory YAML file containing device information.
        groq_model_name (str): Name of the LLM model to use with Groq API.
        groq_temperature (float): Temperature setting for the LLM (controls randomness).
        groq_api_key (str): API key for Groq service (can be empty if provided via environment).
        state_database_file (str): Path to the SQLite database file for storing agent state.
    """

    inventory_file: str = "inventory.yaml"
    groq_model_name: str = "openai/gpt-oss-20b"  # Updated to a current model
    groq_temperature: float = 0.7
    groq_api_key: str = ""
    state_database_file: str = "agent_state.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # This allows extra environment variables
    )


# Create a single, importable instance of the settings
settings = Settings()
