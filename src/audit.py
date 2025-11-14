"""Audit logging and security event tracking."""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class SecurityEventType(Enum):
    """Security event types for audit logging."""
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    
    # Command execution events
    COMMAND_EXECUTED = "command_executed"
    COMMAND_BLOCKED = "command_blocked"
    COMMAND_FAILED = "command_failed"
    
    # Security events
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    VALIDATION_FAILURE = "validation_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    
    # Connection events
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_FAILED = "connection_failed"
    RECONNECT_ATTEMPT = "reconnect_attempt"
    
    # System events
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    MODEL_FALLBACK = "model_fallback"
    ERROR_OCCURRED = "error_occurred"


class AuditLogger:
    """Centralized audit logging with security event tracking."""
    
    def __init__(
        self,
        log_dir: str = "logs",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        log_level: str = "INFO",
    ):
        """Initialize audit logger.
        
        Args:
            log_dir: Directory for log files
            enable_console: Enable console logging
            enable_file: Enable text file logging
            enable_json: Enable JSON structured logging
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Session metadata
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = datetime.now()
        
        # Event counters
        self.event_counts = {event_type: 0 for event_type in SecurityEventType}
        
        # Setup loggers
        self._setup_text_logger(enable_console, enable_file, log_level)
        if enable_json:
            self._setup_json_logger()
    
    def _setup_text_logger(
        self, enable_console: bool, enable_file: bool, log_level: str
    ):
        """Setup text-based logger."""
        self.text_logger = logging.getLogger("network_agent")
        self.text_logger.setLevel(getattr(logging, log_level))
        self.text_logger.handlers.clear()
        
        # Formatter with timestamp, level, and message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.text_logger.addHandler(console_handler)
        
        # File handler (daily rotation would be better for production)
        if enable_file:
            log_file = self.log_dir / f"audit_{self.session_id}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.text_logger.addHandler(file_handler)
    
    def _setup_json_logger(self):
        """Setup JSON structured logger for machine parsing."""
        self.json_log_file = self.log_dir / f"audit_{self.session_id}.jsonl"
        self.json_log_file.touch()
    
    def _write_json_log(self, event_data: dict):
        """Write JSON log entry."""
        try:
            with open(self.json_log_file, 'a') as f:
                json.dump(event_data, f)
                f.write('\n')
        except Exception as e:
            self.text_logger.error(f"Failed to write JSON log: {e}")
    
    def log_event(
        self,
        event_type: SecurityEventType,
        message: str,
        severity: str = "INFO",
        **kwargs
    ):
        """Log a security event with structured data.
        
        Args:
            event_type: Type of security event
            message: Human-readable message
            severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            **kwargs: Additional structured data
        """
        # Increment event counter
        self.event_counts[event_type] += 1
        
        # Build structured event data
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type.value,
            "severity": severity,
            "message": message,
            **kwargs
        }
        
        # Log to text logger
        log_method = getattr(self.text_logger, severity.lower())
        log_message = f"[{event_type.value.upper()}] {message}"
        
        # Add context if provided
        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            log_message += f" | {context_str}"
        
        log_method(log_message)
        
        # Log to JSON logger
        if hasattr(self, 'json_log_file'):
            self._write_json_log(event_data)
    
    # Convenience methods for common events
    
    def log_session_start(self, user: str, device: str, model: str):
        """Log session start."""
        self.log_event(
            SecurityEventType.SESSION_START,
            f"Session started by {user} connecting to {device}",
            severity="INFO",
            user=user,
            device=device,
            model=model,
        )
    
    def log_session_end(self, duration_seconds: float):
        """Log session end."""
        self.log_event(
            SecurityEventType.SESSION_END,
            f"Session ended after {duration_seconds:.2f} seconds",
            severity="INFO",
            duration=duration_seconds,
            total_events=sum(self.event_counts.values()),
        )
    
    def log_connection_established(self, device: str, username: str):
        """Log successful device connection."""
        self.log_event(
            SecurityEventType.CONNECTION_ESTABLISHED,
            f"Connected to {device} as {username}",
            severity="INFO",
            device=device,
            username=username,
        )
    
    def log_connection_failed(self, device: str, username: str, error: str):
        """Log failed device connection."""
        self.log_event(
            SecurityEventType.CONNECTION_FAILED,
            f"Connection failed to {device}: {error}",
            severity="ERROR",
            device=device,
            username=username,
            error=error,
        )
    
    def log_command_executed(
        self, command: str, success: bool, output_length: int = 0, error: str = None
    ):
        """Log command execution."""
        if success:
            self.log_event(
                SecurityEventType.COMMAND_EXECUTED,
                f"Executed: {command}",
                severity="INFO",
                command=command,
                output_length=output_length,
            )
        else:
            self.log_event(
                SecurityEventType.COMMAND_FAILED,
                f"Failed: {command} - {error}",
                severity="ERROR",
                command=command,
                error=error,
            )
    
    def log_command_blocked(self, command: str, reason: str):
        """Log blocked command (security event)."""
        self.log_event(
            SecurityEventType.COMMAND_BLOCKED,
            f"BLOCKED: {command} - {reason}",
            severity="WARNING",
            command=command,
            reason=reason,
        )
    
    def log_prompt_injection(self, query: str, patterns: list[str]):
        """Log prompt injection attempt (critical security event)."""
        self.log_event(
            SecurityEventType.PROMPT_INJECTION_DETECTED,
            f"Prompt injection detected: {patterns}",
            severity="CRITICAL",
            query=query[:200],  # Truncate for log size
            patterns=patterns,
        )
    
    def log_validation_failure(self, query: str, reason: str):
        """Log input validation failure."""
        self.log_event(
            SecurityEventType.VALIDATION_FAILURE,
            f"Validation failed: {reason}",
            severity="WARNING",
            query=query[:200],
            reason=reason,
        )
    
    def log_rate_limit_exceeded(self, limit: int, window: int):
        """Log rate limit exceeded."""
        self.log_event(
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            f"Rate limit exceeded: {limit} requests in {window}s",
            severity="WARNING",
            limit=limit,
            window=window,
        )
    
    def log_model_fallback(self, from_model: str, to_model: str, reason: str):
        """Log model fallback."""
        self.log_event(
            SecurityEventType.MODEL_FALLBACK,
            f"Model fallback: {from_model} → {to_model} ({reason})",
            severity="INFO",
            from_model=from_model,
            to_model=to_model,
            reason=reason,
        )
    
    def get_session_summary(self) -> dict[str, Any]:
        """Get session summary statistics."""
        duration = (datetime.now() - self.session_start).total_seconds()
        return {
            "session_id": self.session_id,
            "duration_seconds": duration,
            "event_counts": {k.value: v for k, v in self.event_counts.items()},
            "total_events": sum(self.event_counts.values()),
        }
    
    def close(self):
        """Close logger and write session summary."""
        duration = (datetime.now() - self.session_start).total_seconds()
        self.log_session_end(duration)
        
        # Write session summary
        summary_file = self.log_dir / f"summary_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(self.get_session_summary(), f, indent=2)