"""
Configuration management module for the network agent.

Handles loading and managing configuration from YAML files.
"""

import yaml
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigManager:
    """Manages application configuration from YAML files."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Dictionary containing configuration data
        """
        if not self.config_path.exists():
            # If config file doesn't exist, use default configuration
            print(f"Warning: Config file {self.config_path} not found. Using default settings.")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML config: {e}")
            return self._get_default_config()
        except Exception as e:
            print(f"Error loading config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings.

        Returns:
            Dictionary with default configuration
        """
        return {
            "security": {
                "max_query_length": 500,
                "max_queries_per_session": 100,
                "allowed_commands": ["show", "display", "get", "dir", "more", "verify"],
                "blocked_keywords": [
                    "reload", "write", "erase", "delete", "no", "clear", 
                    "configure", "conf", "enable", "copy", "format", 
                    "shutdown", "boot", "username", "password", 
                    "crypto", "key", "certificate"
                ]
            },
            "logging": {
                "enable_console": False,
                "enable_file": True,
                "enable_json": True,
                "log_level": "INFO"
            },
            "connection": {
                "max_reconnect_attempts": 3,
                "connection_timeout": 30,
                "read_timeout": 60,
                "command_timeout": 60
            },
            "agent": {
                "default_model": "llama-3.3-70b-versatile",
                "temperature": 0.1,
                "platform_type": "Cisco IOS",
                "verbose_mode": False,
                "api_timeout": 60
            },
            "limits": {
                "max_commands_per_minute": 30,
                "max_session_duration_minutes": 120
            }
        }

    def _validate_config(self):
        """Validate the configuration structure and values."""
        required_sections = ["security", "logging", "connection", "agent", "limits"]
        
        for section in required_sections:
            if section not in self._config:
                print(f"Warning: Missing configuration section '{section}', using defaults")
                self._config[section] = self._get_default_config()[section]

        # Validate specific values
        self._validate_security_config()
        self._validate_logging_config()
        self._validate_connection_config()
        self._validate_agent_config()
        self._validate_limits_config()

    def _validate_security_config(self):
        """Validate security configuration."""
        security = self._config.get("security", {})
        
        # Validate max_query_length
        max_length = security.get("max_query_length", 500)
        if not isinstance(max_length, int) or max_length <= 0:
            print("Warning: max_query_length must be a positive integer, using default 500")
            security["max_query_length"] = 500

        # Validate max_queries_per_session
        max_queries = security.get("max_queries_per_session", 100)
        if not isinstance(max_queries, int) or max_queries <= 0:
            print("Warning: max_queries_per_session must be a positive integer, using default 100")
            security["max_queries_per_session"] = 100

        # Validate allowed_commands
        allowed = security.get("allowed_commands", [])
        if not isinstance(allowed, list):
            print("Warning: allowed_commands must be a list, using default")
            security["allowed_commands"] = ["show", "display", "get", "dir", "more", "verify"]

        # Validate blocked_keywords
        blocked = security.get("blocked_keywords", [])
        if not isinstance(blocked, list):
            print("Warning: blocked_keywords must be a list, using default")
            security["blocked_keywords"] = [
                "reload", "write", "erase", "delete", "no", "clear", 
                "configure", "conf", "enable", "copy", "format", 
                "shutdown", "boot", "username", "password", 
                "crypto", "key", "certificate"
            ]

    def _validate_logging_config(self):
        """Validate logging configuration."""
        logging = self._config.get("logging", {})
        
        # Validate boolean flags
        for flag in ["enable_console", "enable_file", "enable_json"]:
            value = logging.get(flag)
            if not isinstance(value, bool):
                print(f"Warning: logging.{flag} must be boolean, using default")
                logging[flag] = self._get_default_config()["logging"][flag]

        # Validate log_level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = logging.get("log_level", "INFO")
        if log_level not in valid_levels:
            print(f"Warning: log_level must be one of {valid_levels}, using default 'INFO'")
            logging["log_level"] = "INFO"

    def _validate_connection_config(self):
        """Validate connection configuration."""
        connection = self._config.get("connection", {})
        
        # Validate numeric timeouts
        for timeout_name in ["connection_timeout", "read_timeout", "command_timeout"]:
            timeout = connection.get(timeout_name)
            if not isinstance(timeout, int) or timeout <= 0:
                print(f"Warning: connection.{timeout_name} must be a positive integer, using default")
                connection[timeout_name] = self._get_default_config()["connection"][timeout_name]

        # Validate max_reconnect_attempts
        attempts = connection.get("max_reconnect_attempts")
        if not isinstance(attempts, int) or attempts < 0:
            print("Warning: max_reconnect_attempts must be a non-negative integer, using default")
            connection["max_reconnect_attempts"] = 3

    def _validate_agent_config(self):
        """Validate agent configuration."""
        agent = self._config.get("agent", {})
        
        # Validate temperature
        temp = agent.get("temperature", 0.1)
        if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
            print("Warning: temperature must be between 0.0 and 1.0, using default 0.1")
            agent["temperature"] = 0.1

        # Validate api_timeout
        timeout = agent.get("api_timeout", 60)
        if not isinstance(timeout, int) or timeout <= 0:
            print("Warning: api_timeout must be a positive integer, using default 60")
            agent["api_timeout"] = 60

        # Validate verbose_mode
        verbose = agent.get("verbose_mode")
        if not isinstance(verbose, bool):
            print("Warning: verbose_mode must be boolean, using default")
            agent["verbose_mode"] = False

    def _validate_limits_config(self):
        """Validate limits configuration."""
        limits = self._config.get("limits", {})
        
        # Validate max_commands_per_minute
        max_cmd = limits.get("max_commands_per_minute", 30)
        if not isinstance(max_cmd, int) or max_cmd <= 0:
            print("Warning: max_commands_per_minute must be a positive integer, using default 30")
            limits["max_commands_per_minute"] = 30

        # Validate max_session_duration_minutes
        max_duration = limits.get("max_session_duration_minutes", 120)
        if not isinstance(max_duration, int) or max_duration <= 0:
            print("Warning: max_session_duration_minutes must be a positive integer, using default 120")
            limits["max_session_duration_minutes"] = 120

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self._config.get("security", self._get_default_config()["security"])

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get("logging", self._get_default_config()["logging"])

    def get_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration."""
        return self._config.get("connection", self._get_default_config()["connection"])

    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self._config.get("agent", self._get_default_config()["agent"])

    def get_limits_config(self) -> Dict[str, Any]:
        """Get limits configuration."""
        return self._config.get("limits", self._get_default_config()["limits"])

    def get_allowed_commands(self) -> List[str]:
        """Get list of allowed commands."""
        return self.get_security_config().get("allowed_commands", [])

    def get_blocked_keywords(self) -> List[str]:
        """Get list of blocked keywords."""
        return self.get_security_config().get("blocked_keywords", [])

    def get_max_query_length(self) -> int:
        """Get maximum query length allowed."""
        return self.get_security_config().get("max_query_length", 500)

    def get_max_queries_per_session(self) -> int:
        """Get maximum number of queries per session."""
        return self.get_security_config().get("max_queries_per_session", 100)

    def is_console_logging_enabled(self) -> bool:
        """Check if console logging is enabled."""
        return self.get_logging_config().get("enable_console", False)

    def is_file_logging_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return self.get_logging_config().get("enable_file", True)

    def is_json_logging_enabled(self) -> bool:
        """Check if JSON logging is enabled."""
        return self.get_logging_config().get("enable_json", True)

    def get_log_level(self) -> str:
        """Get log level."""
        return self.get_logging_config().get("log_level", "INFO")

    def get_connection_timeout(self) -> int:
        """Get connection timeout value."""
        return self.get_connection_config().get("connection_timeout", 30)

    def get_read_timeout(self) -> int:
        """Get read timeout value."""
        return self.get_connection_config().get("read_timeout", 60)

    def get_command_timeout(self) -> int:
        """Get command timeout value."""
        return self.get_connection_config().get("command_timeout", 60)

    def get_max_reconnect_attempts(self) -> int:
        """Get maximum reconnect attempts."""
        return self.get_connection_config().get("max_reconnect_attempts", 3)

    def get_default_model(self) -> str:
        """Get default model name."""
        return self.get_agent_config().get("default_model", "llama-3.3-70b-versatile")

    def get_temperature(self) -> float:
        """Get temperature setting."""
        return self.get_agent_config().get("temperature", 0.1)

    def get_platform_type(self) -> str:
        """Get platform type."""
        return self.get_agent_config().get("platform_type", "Cisco IOS")

    def is_verbose_mode(self) -> bool:
        """Check if verbose mode is enabled."""
        return self.get_agent_config().get("verbose_mode", False)

    def get_api_timeout(self) -> int:
        """Get API timeout value."""
        return self.get_agent_config().get("api_timeout", 60)

    def get_max_commands_per_minute(self) -> int:
        """Get maximum commands per minute."""
        return self.get_limits_config().get("max_commands_per_minute", 30)

    def get_max_session_duration_minutes(self) -> int:
        """Get maximum session duration in minutes."""
        return self.get_limits_config().get("max_session_duration_minutes", 120)

    def reload_config(self):
        """Reload configuration from file."""
        self._config = self._load_config()
        self._validate_config()

    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration with new values.

        Args:
            new_config: Dictionary with new configuration values
        """
        # Deep merge the new config with existing one
        def deep_merge(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_merge(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_merge(self._config, new_config)
        self._validate_config()