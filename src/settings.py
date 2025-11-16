"""Simplified configuration management using Pydantic BaseSettings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration for the network agent.
    Settings are loaded from environment variables.
    """

    # Model settings
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    api_timeout: int = 60

    # Security settings
    max_query_length: int = 500
    max_queries_per_session: int = 100
    allowed_commands: List[str] = ["show", "display", "get", "dir", "more", "verify"]
    blocked_keywords: List[str] = [
        "reload",
        "write",
        "erase",
        "delete",
        "no",
        "clear",
        "configure",
        "conf",
        "enable",
        "copy",
        "format",
        "shutdown",
        "boot",
        "username",
        "password",
        "crypto",
        "key",
        "certificate",
    ]

    # Logging settings
    verbose: bool = False
    log_level: str = "INFO"
    log_directory: str = "logs"
    enable_console_logging: bool = True
    enable_file_logging: bool = True

    # Connection settings
    connection_timeout: int = 30
    read_timeout: int = 60
    command_timeout: int = 60
    banner_timeout: int = 15
    global_delay_factor: int = 2

    # API Keys
    groq_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
