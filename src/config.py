"""
Unified configuration management system for the network agent.

This module provides a single configuration interface that combines
application settings from YAML files with environment variables and secrets.
"""

from typing import Dict, Any, List, Optional
import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv


class SecurityConfig(BaseModel):
    max_query_length: int = 500
    max_queries_per_session: int = 100
    allowed_commands: List[str] = ["show", "display", "get", "dir", "more", "verify"]
    blocked_keywords: List[str] = [
        "reload", "write", "erase", "delete", "no", "clear",
        "configure", "conf", "enable", "copy", "format",
        "shutdown", "boot", "username", "password",
        "crypto", "key", "certificate"
    ]


class LoggingConfig(BaseModel):
    enable_console: bool = False
    enable_file: bool = True
    enable_json: bool = True
    log_level: str = "INFO"
    log_directory: str = "logs"


class ConnectionConfig(BaseModel):
    max_reconnect_attempts: int = 3
    connection_timeout: int = 30
    read_timeout: int = 60
    command_timeout: int = 60
    banner_timeout: int = 15
    global_delay_factor: int = 2


class AgentConfig(BaseModel):
    default_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    platform_type: str = "Cisco IOS"
    verbose_mode: bool = False
    api_timeout: int = 60


class LimitsConfig(BaseModel):
    max_commands_per_minute: int = 30
    max_session_duration_minutes: int = 120
    rate_limit_window_seconds: int = 60


class AppConfig(BaseModel):
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()  # Load environment variables

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from YAML file with environment overrides."""
        # Load base config from YAML
        if not self.config_path.exists():
            print(f"Warning: Config file {self.config_path} not found. Using default settings.")
            base_config = {}
        else:
            try:
                with open(self.config_path, 'r') as f:
                    base_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                base_config = {}

        # Apply environment overrides
        env_overrides = {
            "security": {
                "max_query_length": self._get_env_int("MAX_QUERY_LENGTH"),
                "max_queries_per_session": self._get_env_int("MAX_QUERIES_PER_SESSION"),
            },
            "logging": {
                "log_level": os.getenv("LOG_LEVEL"),
                "enable_console": self._get_env_bool("ENABLE_CONSOLE"),
                "enable_file": self._get_env_bool("ENABLE_FILE"),
                "enable_json": self._get_env_bool("ENABLE_JSON"),
                "log_directory": os.getenv("LOG_DIRECTORY"),
            },
            "connection": {
                "max_reconnect_attempts": self._get_env_int("MAX_RECONNECT_ATTEMPTS"),
                "connection_timeout": self._get_env_int("CONNECTION_TIMEOUT"),
                "read_timeout": self._get_env_int("READ_TIMEOUT"),
                "command_timeout": self._get_env_int("COMMAND_TIMEOUT"),
                "banner_timeout": self._get_env_int("BANNER_TIMEOUT"),
                "global_delay_factor": self._get_env_int("GLOBAL_DELAY_FACTOR"),
            },
            "agent": {
                "default_model": os.getenv("DEFAULT_MODEL"),
                "temperature": self._get_env_float("TEMPERATURE"),
                "platform_type": os.getenv("PLATFORM_TYPE"),
                "verbose_mode": self._get_env_bool("VERBOSE_MODE"),
                "api_timeout": self._get_env_int("API_TIMEOUT"),
            },
            "limits": {
                "max_commands_per_minute": self._get_env_int("MAX_COMMANDS_PER_MINUTE"),
                "max_session_duration_minutes": self._get_env_int("MAX_SESSION_DURATION_MINUTES"),
                "rate_limit_window_seconds": self._get_env_int("RATE_LIMIT_WINDOW_SECONDS"),
            }
        }

        # Merge environment overrides (only non-None values)
        def merge_env_overrides(base, overrides):
            for key, value in overrides.items():
                if value is not None:
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        merge_env_overrides(base[key], value)
                    else:
                        base[key] = value
            return base

        merge_env_overrides(base_config, env_overrides)

        return AppConfig(**base_config)

    def _get_env_int(self, key: str) -> Optional[int]:
        """Get an integer environment variable."""
        value = os.getenv(key)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                print(f"Warning: Environment variable {key} is not a valid integer: {value}")
                return None
        return None

    def _get_env_float(self, key: str) -> Optional[float]:
        """Get a float environment variable."""
        value = os.getenv(key)
        if value is not None:
            try:
                return float(value)
            except ValueError:
                print(f"Warning: Environment variable {key} is not a valid float: {value}")
                return None
        return None

    def _get_env_bool(self, key: str) -> Optional[bool]:
        """Get a boolean environment variable."""
        value = os.getenv(key)
        if value is not None:
            # Convert common string representations to boolean
            value = value.lower().strip()
            if value in ('true', '1', 'yes', 'on'):
                return True
            elif value in ('false', '0', 'no', 'off', ''):
                return False
            else:
                print(f"Warning: Environment variable {key} is not a valid boolean: {value}")
                return None
        return None

    @property
    def app(self) -> AppConfig:
        return self._config

    @property
    def groq_api_key(self) -> str:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Error: Set GROQ_API_KEY in .env file")
        return api_key

    @property
    def device_password(self) -> str:
        password = os.getenv("DEVICE_PASSWORD")
        if password:
            return password
        import getpass
        return getpass.getpass("Password: ")

    def reload(self):
        """Reload configuration from file."""
        self._config = self._load_config()

    def validate(self) -> List[str]:
        """Validate the entire configuration and return a list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate security settings
        if self.app.security.max_query_length <= 0:
            errors.append("security.max_query_length must be positive")

        if not self.app.security.allowed_commands:
            errors.append("security.allowed_commands cannot be empty")

        # Validate logging settings
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.app.logging.log_level not in valid_log_levels:
            errors.append(f"logging.log_level must be one of {valid_log_levels}")

        # Validate connection settings
        if self.app.connection.connection_timeout <= 0:
            errors.append("connection.connection_timeout must be positive")

        if self.app.connection.read_timeout <= 0:
            errors.append("connection.read_timeout must be positive")

        if self.app.connection.command_timeout <= 0:
            errors.append("command_timeout must be positive")

        if self.app.connection.max_reconnect_attempts < 0:
            errors.append("max_reconnect_attempts cannot be negative")

        # Validate agent settings
        if not (0 <= self.app.agent.temperature <= 1):
            errors.append("agent.temperature must be between 0 and 1")

        if self.app.agent.api_timeout <= 0:
            errors.append("agent.api_timeout must be positive")

        # Validate limits settings
        if self.app.limits.max_commands_per_minute <= 0:
            errors.append("limits.max_commands_per_minute must be positive")

        if self.app.limits.max_session_duration_minutes <= 0:
            errors.append("limits.max_session_duration_minutes must be positive")

        return errors

    def update(self, section: str, key: str, value: Any) -> bool:
        """Update a configuration value.

        Args:
            section: Configuration section (e.g., 'security', 'logging')
            key: Configuration key within the section
            value: New value to set

        Returns:
            True if update was successful, False otherwise
        """
        try:
            section_obj = getattr(self.app, section)
            setattr(section_obj, key, value)
            return True
        except (AttributeError, ValueError):
            return False