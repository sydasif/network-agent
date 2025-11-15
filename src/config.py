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


class ConnectionConfig(BaseModel):
    max_reconnect_attempts: int = 3
    connection_timeout: int = 30
    read_timeout: int = 60
    command_timeout: int = 60


class AgentConfig(BaseModel):
    default_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    platform_type: str = "Cisco IOS"
    verbose_mode: bool = False
    api_timeout: int = 60


class LimitsConfig(BaseModel):
    max_commands_per_minute: int = 30
    max_session_duration_minutes: int = 120


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
        """Load configuration from YAML file with fallback to defaults."""
        if not self.config_path.exists():
            print(f"Warning: Config file {self.config_path} not found. Using default settings.")
            return AppConfig()
            
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            return AppConfig(**config_data)
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return AppConfig()
    
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