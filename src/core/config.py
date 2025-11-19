"""Simplified configuration settings for the application.

This module provides a simplified configuration system using Pydantic Settings.
It loads configuration values from environment variables or a .env file and
exposes a single settings instance that can be imported throughout the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.

    This class defines all configurable parameters for the application.
    Settings can be overridden by environment variables or values in a .env file.

    Attributes:
        nornir_inventory_dir (str): Path to the Nornir inventory directory.
        groq_model_name (str): Name of the LLM model to use with Groq API.
        groq_temperature (float): Temperature setting for the LLM (controls randomness).
        groq_api_key (str): API key for Groq service (can be empty if provided via environment).
    """

    nornir_inventory_dir: str = "inventory"
    groq_model_name: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.3
    groq_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Create a single, importable instance of the settings
settings = Settings()
