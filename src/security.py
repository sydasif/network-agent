"""Command security policy for the network agent."""

from .settings import settings


class CommandSecurityPolicy:
    """Enforces security policies for command execution."""

    def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a command against all security policies.

        Args:
            command: The command to validate.

        Returns:
            A tuple (is_valid, reason).
        """
        command_stripped = command.strip()
        command_lower = command_stripped.lower()

        if not command_stripped:
            return False, "Empty command"

        if error_reason := self._check_blocked_keywords(command_stripped, command_lower):
            return False, error_reason

        if error_reason := self._check_allowed_prefix(command_stripped, command_lower):
            return False, error_reason

        if error_reason := self._check_command_chaining(command_stripped, command_lower):
            return False, error_reason

        return True, ""

    def _check_blocked_keywords(self, command_stripped: str, command_lower: str) -> str | None:
        """Check for blocked keywords."""
        for blocked in settings.blocked_keywords:
            if blocked in command_lower:
                return f"Blocked keyword '{blocked}'"
        return None

    def _check_allowed_prefix(self, command_stripped: str, command_lower: str) -> str | None:
        """Check for allowed command prefixes."""
        if not any(command_lower.startswith(prefix) for prefix in settings.allowed_commands):
            return "Command does not start with an allowed prefix"
        return None

    def _check_command_chaining(self, command_stripped: str, command_lower: str) -> str | None:
        """Check for command chaining."""
        if ";" in command_stripped:
            return "Semicolon command chaining is not allowed"
        if "|" in command_stripped:
            allowed_pipes = ["| include", "| begin", "| section", "| exclude"]
            if not any(pipe in command_lower for pipe in allowed_pipes):
                return "Unsupported pipe command"
        return None
