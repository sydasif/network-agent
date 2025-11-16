"""Unified validation pipeline for network automation."""

import logging
import re
from typing import Optional

from .audit import AuditLogger, SecurityEventType
from .exceptions import BlockedContentError, QueryTooLongError, CommandBlockedError
from .settings import settings


logger = logging.getLogger("net_agent.validation")


class ValidationPipeline:
    """Unified validation pipeline that combines all validation checks."""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        self.audit_logger = audit_logger
    
    def validate_query(self, query: str) -> None:
        """Validate a user query using all validation rules.
        
        Args:
            query: User input query
            
        Raises:
            QueryTooLongError: If query exceeds length limits
            BlockedContentError: If query contains blocked content
        """
        # Check if query is empty
        if not query or not query.strip():
            if self.audit_logger:
                self.audit_logger.log(
                    SecurityEventType.ERROR,
                    f"Validation failed: Empty query. Query: {query[:200]}",
                    severity="warning",
                )
            raise BlockedContentError(query, "empty")

        # Check length limits
        if len(query) > settings.max_query_length:
            # Log validation failure to audit system
            if self.audit_logger:
                self.audit_logger.log(
                    SecurityEventType.ERROR,
                    f"Validation failed: Length exceeded. Query: {query[:200]}",
                    severity="warning",
                )
            raise QueryTooLongError(length=len(query), max_length=settings.max_query_length)

        # Check for blocked patterns
        query_lower = query.lower()
        for pattern in settings.blocked_keywords:
            if re.search(pattern, query_lower, re.IGNORECASE):
                # Log validation failure to audit system
                if self.audit_logger:
                    self.audit_logger.log(
                        SecurityEventType.ERROR,
                        f"Validation failed: Blocked pattern: {pattern}. Query: {query[:200]}",
                        severity="critical",
                    )
                raise BlockedContentError(content=query, pattern=pattern)
    
    def validate_command(self, command: str) -> None:
        """Validate a command using security policy rules.
        
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
                if self.audit_logger:
                    self.audit_logger.log_command_blocked(command, reason)
                raise CommandBlockedError(command, reason)

        # Check for allowed command prefixes
        if not any(
            command_lower.startswith(prefix) for prefix in settings.allowed_commands
        ):
            reason = "Command does not start with an allowed prefix"
            if self.audit_logger:
                self.audit_logger.log_command_blocked(command, reason)
            raise CommandBlockedError(command, reason)

        # Check for command chaining
        if ";" in command_stripped:
            reason = "Semicolon command chaining is not allowed"
            if self.audit_logger:
                self.audit_logger.log_command_blocked(command, reason)
            raise CommandBlockedError(command, reason)
            
        if "|" in command_stripped:
            allowed_pipes = ["| include", "| begin", "| section", "| exclude"]
            if not any(pipe in command_lower for pipe in allowed_pipes):
                reason = "Unsupported pipe command"
                if self.audit_logger:
                    self.audit_logger.log_command_blocked(command, reason)
                raise CommandBlockedError(command, reason)
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize query by removing/escaping dangerous content.

        Args:
            query: Raw user input

        Returns:
            Sanitized query safe for LLM processing
        """
        # Remove null bytes
        query = query.replace("\x00", "")

        # Remove excessive whitespace
        query = " ".join(query.split())

        # Remove HTML/XML tags
        query = re.sub(r"<[^>]+>", "", query)

        # Escape backticks (prevent code block injection)
        query = query.replace("`", "'")

        # Limit consecutive special characters
        query = re.sub(r"([^Ws])\1{3,}", r"\1\1", query)

        return query.strip()