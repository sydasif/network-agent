"""Core validation pipeline module."""

import re


class ValidationPipeline:
    """Validates and sanitizes network commands."""

    def __init__(self):
        # Dangerous commands that should be blocked
        self.dangerous_commands = [
            r"write\s+erase",
            r"delete\s+",
            r"format\s+",
            r"no\s+shutdown",
            r"configure\s+terminal",
            r"wr\s+erase",
            r"del\s+",
            r"format\s",
            r"reload",
            r"no shutdown",
            r"ip route 0.0.0.0 0.0.0.0 null",
            r"username\s+\w+\s+privilege\s+15",
            r"enable secret",
            r"secret\s+0",
            r"no ip domain-lookup",
            r"default interface",
            r"clear counters",
        ]

        # Commands that should be allowed
        self.allowed_commands = [
            r"show\s+",
            r"ping\s+",
            r"traceroute\s+",
            r"debug\s+",
            r"terminal\s+",
        ]

    def sanitize_query(self, query: str) -> str:
        """Sanitize the query to remove potentially harmful elements."""
        # Remove potentially dangerous characters/sequences
        sanitized = re.sub(r"[;|&]", " ", query)  # Remove command separators
        sanitized = re.sub(r"`.*?`", "", sanitized)  # Remove command substitution
        sanitized = re.sub(r"\$\(.*?\)", "", sanitized)  # Remove command substitution
        sanitized = re.sub(r"\\.*", "", sanitized)  # Remove escape sequences

        return sanitized.strip()

    def validate_query(self, query: str) -> bool:
        """Validate if the query is safe to execute."""
        query_lower = query.lower()

        # Check for dangerous commands
        for dangerous_cmd in self.dangerous_commands:
            if re.search(dangerous_cmd, query_lower):
                raise ValueError(f"Potentially dangerous command detected: {query}")

        # Check if command is allowed
        is_allowed = False
        for allowed_cmd in self.allowed_commands:
            if re.search(allowed_cmd, query_lower):
                is_allowed = True
                break

        if not is_allowed:
            raise ValueError(f"Command not in allowed list: {query}")

        return True
