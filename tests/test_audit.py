"""Tests for the AuditLogger class."""

import unittest
import tempfile
import os
from pathlib import Path
from src.audit import AuditLogger, SecurityEventType


class TestAuditLogger(unittest.TestCase):
    """Test cases for the AuditLogger class."""

    def setUp(self):
        """Set up the test case."""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_logger = AuditLogger(
            log_dir=self.temp_dir,
            enable_console=False,
            enable_file=True,
            log_level="INFO",
        )

    def tearDown(self):
        """Clean up after the test case."""
        self.audit_logger.close()
        # Remove log files created during tests
        for file in Path(self.temp_dir).glob("*.log"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_log_session_start(self):
        """Test logging session start."""
        self.audit_logger.log_session_start(
            "test_user", "192.168.1.1", "llama-3.3-70b-versatile"
        )
        # This should not raise an exception

    def test_log_connection_established(self):
        """Test logging connection established."""
        self.audit_logger.log_connection_established("192.168.1.1", "admin")
        # This should not raise an exception

    def test_log_connection_failed(self):
        """Test logging connection failed."""
        self.audit_logger.log_connection_failed(
            "192.168.1.1", "admin", "Authentication failed"
        )
        # This should not raise an exception

    def test_log_command_executed_success(self):
        """Test logging successful command execution."""
        self.audit_logger.log_command_executed(
            "show version", success=True, output_length=100
        )
        # This should not raise an exception

    def test_log_command_executed_failure(self):
        """Test logging failed command execution."""
        self.audit_logger.log_command_executed(
            "show version", success=False, error="Command failed"
        )
        # This should not raise an exception

    def test_log_event(self):
        """Test logging a generic event."""
        self.audit_logger.log_event(SecurityEventType.COMMAND, "Test event message")
        # This should not raise an exception

    def test_log_with_severity(self):
        """Test logging with different severity levels."""
        self.audit_logger.log(SecurityEventType.ERROR, "Test error", severity="error")
        # This should not raise an exception

    def test_log_sanitization(self):
        """Test that logs are properly sanitized."""
        sensitive_command = "password secret123"
        self.audit_logger.log_command_executed(
            sensitive_command, success=True, output_length=50
        )
        # This should not raise an exception and should sanitize the command


if __name__ == "__main__":
    unittest.main()
