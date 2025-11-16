"""Audit logging and security event tracking."""

import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .sensitive_data import SensitiveDataProtector


class SecurityEventType(Enum):
    """Simplified security event types for audit logging."""
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"
    CONNECTION = "CONNECTION"
    COMMAND = "COMMAND"
    ERROR = "ERROR"


class AuditLogger:
    """Simplified, centralized audit logging."""

    def __init__(
        self,
        log_dir: str = "logs",
        enable_console: bool = True,
        enable_file: bool = True,
        log_level: str = "INFO",
    ):
        """Initialize audit logger.

        Args:
            log_dir: Directory for log files
            enable_console: Enable console logging
            enable_file: Enable text file logging
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_protector = SensitiveDataProtector()

        self.logger = logging.getLogger("net_agent_audit")
        self.logger.setLevel(getattr(logging, log_level.upper(), "INFO"))
        self.logger.handlers.clear()

        formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        if enable_file:
            log_file = self.log_dir / f"audit_{self.session_id}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log(self, event_type: SecurityEventType, message: str, severity: str = "info"):
        """Log a security event.

        Args:
            event_type: The type of event.
            message: The log message.
            severity: The log level ('info', 'warning', 'error').
        """
        log_method = getattr(self.logger, severity, self.logger.info)
        log_method(f"{event_type.value}: {message}")

    def log_session_start(self, user: str, device: str, model: str):
        """Log session start."""
        safe_user = self.data_protector.sanitize_for_logging(user)
        safe_device = self.data_protector.sanitize_for_logging(device)
        self.log(
            SecurityEventType.SESSION_START,
            f"Session started by {safe_user} connecting to {safe_device} with model {model}",
        )

    def log_connection_established(self, device: str, username: str):
        """Log successful device connection."""
        safe_device = self.data_protector.sanitize_for_logging(device)
        safe_username = self.data_protector.sanitize_for_logging(username)
        self.log(
            SecurityEventType.CONNECTION,
            f"Connected to {safe_device} as {safe_username}",
        )

    def log_connection_failed(self, device: str, username: str, error: str):
        """Log failed device connection."""
        safe_device = self.data_protector.sanitize_for_logging(device)
        safe_username = self.data_protector.sanitize_for_logging(username)
        safe_error = self.data_protector.sanitize_error(error)
        self.log(
            SecurityEventType.ERROR,
            f"Connection failed to {safe_device} as {safe_username}: {safe_error}",
            severity="error",
        )

    def log_command_blocked(self, command: str, reason: str):
        """Log blocked command."""
        safe_command = self.data_protector.sanitize_command(command)
        safe_reason = self.data_protector.sanitize_for_logging(reason)
        self.log(
            SecurityEventType.COMMAND,
            f"BLOCKED: '{safe_command}' | Reason: {safe_reason}",
            severity="warning",
        )

    def log_command_executed(self, command: str, success: bool, output_length: int = 0, error: str = None):
        """Log command execution."""
        safe_command = self.data_protector.sanitize_command(command)
        if success:
            self.log(
                SecurityEventType.COMMAND,
                f"SUCCESS: '{safe_command}' | Output length: {output_length}",
            )
        else:
            safe_error = self.data_protector.sanitize_error(error) if error else "Unknown error"
            self.log(
                SecurityEventType.COMMAND,
                f"FAILURE: '{safe_command}' | Error: {safe_error}",
                severity="error",
            )

    def log_event(self, event_type: SecurityEventType, message: str, severity: str = "info", **kwargs):
        """Generic event logger for other events."""
        self.log(event_type, message, severity)

    def close(self):
        """Close the logger."""
        self.log(SecurityEventType.SESSION_END, "Session ended.")
        logging.shutdown()