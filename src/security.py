"""Command security policy for the network agent."""

from .exceptions import CommandBlockedError
from .settings import settings


class CommandSecurityPolicy:
    """Enforces security policies for command execution."""

    def validate_command(self, command: str) -> None:
        """
        Validate a command against all security policies.

        Args:
            command: The command to validate.

        Raises:
            CommandBlockedError: If the command fails validation.
        """
        command_stripped = command.strip()
        command_lower = command_stripped.lower()

        if not command_stripped:
            raise CommandBlockedError(command, "Empty command")

        # Check for blocked keywords
        for blocked in settings.blocked_keywords:
            if blocked in command_lower:
                reason = f"Blocked keyword '{blocked}'"
                raise CommandBlockedError(command, reason)

        # Check for allowed command prefixes
        if not any(
            command_lower.startswith(prefix) for prefix in settings.allowed_commands
        ):
            reason = "Command does not start with an allowed prefix"
            raise CommandBlockedError(command, reason)

        # Check for command chaining
        if ";" in command_stripped:
            reason = "Semicolon command chaining is not allowed"
            raise CommandBlockedError(command, reason)

        if "|" in command_stripped:
            allowed_pipes = ["| include", "| begin", "| section", "| exclude"]
            if not any(pipe in command_lower for pipe in allowed_pipes):
                reason = "Unsupported pipe command"
                raise CommandBlockedError(command, reason)
