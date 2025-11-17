"""Centralized configuration settings for the application."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loads settings from .env file or environment variables."""
    inventory_file: str = "inventory.yaml"
    spacy_model: str = "en_core_web_sm"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # This allows extra environment variables


# Create a single, importable instance of the settings
settings = Settings()