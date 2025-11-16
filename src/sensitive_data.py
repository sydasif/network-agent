"""Sensitive data protection and sanitization."""

import re
from typing import Any


class SensitiveDataProtector:
    """Protect sensitive data in logs, errors, and outputs."""

    # Define patterns for sensitive data detection
    # Order matters: more specific patterns should come first to avoid conflicts
    SECRET_PATTERNS = [
        r'password\s*[:=]?\s*["\']?([^"\'\s]{4,})["\']?',  # Handles "password: value", "password=value", "password value"
        r'secret\s*[:=]?\s*["\']?([^"\'\s]{4,})["\']?',   # Handles "secret: value", "secret=value", "secret value"
        r'key\s*[:=]?\s*["\']?([^"\'\s]{4,})["\']?',      # Handles "key: value", "key=value", "key value"
    ]

    API_KEY_PATTERN = r'gsk_[a-zA-Z0-9]{32,}'  # Groq API key pattern

    @staticmethod
    def sanitize_for_logging(text: str) -> str:
        """Sanitize text before logging to remove sensitive data.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text with sensitive data redacted
        """
        if not text:
            return text

        # Find all matches first to avoid recursive replacement issues
        all_matches = []

        # Find API key matches
        for match in re.finditer(SensitiveDataProtector.API_KEY_PATTERN, text, flags=re.IGNORECASE):
            all_matches.append((match.start(), match.end(), '[API_KEY_REDACTED]'))

        # Find secret matches
        for pattern in SensitiveDataProtector.SECRET_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                all_matches.append((match.start(), match.end(), '[SECRET_REDACTED]'))

        # Sort matches by start position in reverse order to avoid index shifting issues during replacement
        all_matches.sort(key=lambda x: x[0], reverse=True)

        # Apply replacements from end to start to avoid affecting indices
        result = text
        for start, end, replacement in all_matches:
            result = result[:start] + replacement + result[end:]

        return result

    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitize command for safe logging.

        Args:
            command: Command to sanitize

        Returns:
            Sanitized command
        """
        return SensitiveDataProtector.sanitize_for_logging(command)

    @staticmethod
    def sanitize_output(output: str, max_length: int = 1000) -> str:
        """Sanitize command output for safe logging.

        Args:
            output: Output to sanitize
            max_length: Maximum length to log (0 = no limit)

        Returns:
            Sanitized output, possibly truncated
        """
        # Sanitize sensitive data
        sanitized = SensitiveDataProtector.sanitize_for_logging(output)

        # Truncate if needed
        if max_length > 0 and len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + f"\n... [TRUNCATED: {len(output) - max_length} more chars]"

        return sanitized

    @staticmethod
    def sanitize_error(error: str) -> str:
        """Sanitize error message for safe display/logging.

        Args:
            error: Error message to sanitize

        Returns:
            Sanitized error message
        """
        return SensitiveDataProtector.sanitize_for_logging(error)

    @staticmethod
    def mask_password(password: str) -> str:
        """Mask password for display purposes.

        Args:
            password: Password to mask

        Returns:
            Masked password (e.g., "****")
        """
        if not password:
            return ""
        return "****" if len(password) <= 4 else "*" * len(password)

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """Mask API key for display purposes.

        Args:
            api_key: API key to mask

        Returns:
            Masked API key (show first/last 4 chars)
        """
        if not api_key or len(api_key) < 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"