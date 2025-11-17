"""Core sensitive data handling module."""

import re


class SensitiveDataHandler:
    """Handles sanitization of sensitive information from CLI output."""

    def __init__(self):
        # Patterns to identify sensitive data
        self.sensitive_patterns = [
            r"password\s+\S+",  # password followed by value
            r"secret\s+\d+\s+\S+",  # secret with level and value
            r"enable\s+secret\s+\S+",  # enable secret
            r"username\s+\S+\s+password\s+\S+",  # username with password
            r"key\s+\d+\s+\S+",  # key with value
            r"community\s+\S+\s+(RO|RW)",  # SNMP community strings
            r"(md5|sha)\s+\S+",  # Hash values that might be secrets
        ]

    def clean_output(self, output: str) -> str:
        """Clean sensitive information from CLI output."""
        cleaned_output = output

        for pattern in self.sensitive_patterns:
            # Replace sensitive data with [REDACTED]
            cleaned_output = re.sub(
                pattern,
                lambda m: m.group(0).split()[0] + " [REDACTED]",
                cleaned_output,
                flags=re.IGNORECASE,
            )

        return cleaned_output
