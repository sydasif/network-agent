"""Custom exception hierarchy for the network agent."""

class NetworkAgentError(Exception):
    """Base exception class for the network agent."""
    pass


class ConnectionError(NetworkAgentError):
    """Base exception for connection-related errors."""
    pass


class ConnectionTimeout(ConnectionError):
    """Raised when a connection times out."""
    def __init__(self, host: str, timeout: float, message: str = None):
        self.host = host
        self.timeout = timeout
        self.message = message or f"Connection to {host} timed out after {timeout}s"
        super().__init__(self.message)


class AuthenticationFailed(ConnectionError):
    """Raised when authentication fails."""
    def __init__(self, host: str, username: str, message: str = None):
        self.host = host
        self.username = username
        self.message = message or f"Authentication failed for {username}@{host}"
        super().__init__(self.message)


class CommandError(NetworkAgentError):
    """Base exception for command-related errors."""
    pass


class CommandBlockedError(CommandError):
    """Raised when a command is blocked by security policy."""
    def __init__(self, command: str, reason: str):
        self.command = command
        self.reason = reason
        self.message = f"Command '{command}' is blocked: {reason}"
        super().__init__(self.message)

    def __str__(self):
        return self.message


class CommandExecutionError(CommandError):
    """Raised when a command fails to execute."""
    def __init__(self, command: str, reason: str = None):
        self.command = command
        self.reason = reason
        self.message = f"Command '{command}' failed to execute"
        if reason:
            self.message += f": {reason}"
        super().__init__(self.message)

    def __str__(self):
        return self.message


class CommandValidationError(CommandError):
    """Raised when a command fails validation."""
    def __init__(self, command: str, reason: str):
        self.command = command
        self.reason = reason
        self.message = f"Command '{command}' failed validation: {reason}"
        super().__init__(self.message)


class ValidationError(NetworkAgentError):
    """Base exception for validation-related errors."""
    pass


class QueryTooLongError(ValidationError):
    """Raised when a query exceeds the maximum allowed length."""
    def __init__(self, length: int, max_length: int):
        self.length = length
        self.max_length = max_length
        self.message = f"Query too long ({length} characters), maximum allowed: {max_length} characters"
        super().__init__(self.message)

    def __str__(self):
        return self.message


class BlockedContentError(ValidationError):
    """Raised when a query contains blocked content."""
    def __init__(self, content: str, pattern: str):
        self.content = content
        self.pattern = pattern
        self.message = f"Query contains blocked content matching pattern: {pattern}"
        super().__init__(self.message)

    def __str__(self):
        return self.message


class SuspiciousPatternError(ValidationError):
    """Raised when a query contains suspicious patterns."""
    def __init__(self, content: str, pattern: str):
        self.content = content
        self.pattern = pattern
        self.message = f"Query contains suspicious pattern: {pattern}"
        super().__init__(self.message)


class AgentError(NetworkAgentError):
    """Base exception for agent-related errors."""
    pass


class ModelError(AgentError):
    """Raised when there's an error with the language model."""
    pass


class TimeoutError(AgentError):
    """Raised when an operation times out."""
    def __init__(self, operation: str, timeout: float):
        self.operation = operation
        self.timeout = timeout
        self.message = f"Operation '{operation}' timed out after {timeout}s"
        super().__init__(self.message)