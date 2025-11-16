from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CommandResult:
    """Result of a command execution."""

    command: str
    output: str
    success: bool
    timestamp: datetime
    execution_time: float  # seconds
    error: Optional[str] = None

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} {self.command} ({self.execution_time:.2f}s)"


@dataclass
class ConnectionInfo:
    """Information about device connection."""

    hostname: str
    username: str
    device_type: str = "cisco_ios"
    port: int = 22


@dataclass
class ConnectionStatus:
    """Current connection status."""

    connected: bool
    device: Optional[str] = None
    established_at: Optional[datetime] = None

    def uptime_seconds(self) -> float:
        if self.established_at:
            return (datetime.now() - self.established_at).total_seconds()
        return 0.0


@dataclass
class ValidationResult:
    """Result of input validation."""

    valid: bool
    original_query: str
    sanitized_query: Optional[str] = None
    error_message: Optional[str] = None
    blocked_patterns: Optional[list[str]] = None


@dataclass
class AgentConfig:
    """Agent configuration."""

    model_name: str
    temperature: float
    timeout: int
    verbose: bool


@dataclass
class SecurityPolicy:
    """Security policy configuration."""

    allowed_commands: list[str]
    blocked_keywords: list[str]
    max_query_length: int
