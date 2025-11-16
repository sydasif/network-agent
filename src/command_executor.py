"""Command execution and validation for network devices."""

import logging
import re
from typing import Optional

from .security import CommandSecurityPolicy
from .audit import AuditLogger, SecurityEventType
from .exceptions import CommandBlockedError
from .sensitive_data import SensitiveDataProtector


logger = logging.getLogger("net_agent.command_executor")


class CommandExecutor:
    """Execute commands on network devices after validation."""

    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize command executor."""
        self.audit_logger = audit_logger
        self.security_policy = CommandSecurityPolicy()
        self.data_protector = SensitiveDataProtector()

    def execute_command(self, command: str, session) -> str:
        """Execute a command after validation."""
        # Validate command
        try:
            self.security_policy.validate_command(command)
        except CommandBlockedError as e:
            if self.audit_logger:
                self.audit_logger.log_command_blocked(command, e.reason)
            return f"⚠ BLOCKED: {e.reason}"

        return self._execute_validated_command(command, session)

    def _execute_validated_command(self, command: str, session) -> str:
        """Execute a validated command on the specified device."""
        try:
            logger.debug("Executing: %s", command)
            output = session.execute_command(command)
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command, success=True, output_length=len(output)
                )
            return output
        except ConnectionError as e:
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command, success=False, error=str(e)
                )
            return f"❌ Connection Error: {e}"
        except Exception as e:
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command, success=False, error=str(e)
                )
            return f"⚠️ Error: {e}"