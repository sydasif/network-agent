"""Tests for the CommandSecurityPolicy class."""

import unittest
from src.security import CommandSecurityPolicy
from src.exceptions import CommandBlockedError


class TestCommandSecurityPolicy(unittest.TestCase):
    """Test cases for the CommandSecurityPolicy class."""

    def setUp(self):
        """Set up the test case."""
        self.policy = CommandSecurityPolicy()

    def test_validate_command_valid(self):
        """Test that a valid command passes validation."""
        # Should not raise any exception
        try:
            self.policy.validate_command("show version")
            self.assertTrue(True)  # No exception raised
        except Exception:
            self.fail("validate_command raised an exception unexpectedly!")

    def test_validate_command_empty(self):
        """Test that an empty command fails validation."""
        with self.assertRaises(CommandBlockedError):
            self.policy.validate_command("")

    def test_validate_command_blocked_keyword(self):
        """Test that a command with a blocked keyword fails validation."""
        with self.assertRaises(CommandBlockedError):
            self.policy.validate_command("reload")

    def test_validate_command_not_allowed_prefix(self):
        """Test that a command with a not allowed prefix fails validation."""
        with self.assertRaises(CommandBlockedError):
            self.policy.validate_command("configure terminal")

    def test_validate_command_chaining_semicolon(self):
        """Test that a command with semicolon chaining fails validation."""
        with self.assertRaises(CommandBlockedError):
            self.policy.validate_command("show version; show ip interface brief")

    def test_validate_command_chaining_pipe(self):
        """Test that a command with an unsupported pipe command fails validation."""
        with self.assertRaises(CommandBlockedError):
            self.policy.validate_command("show version | grep test")

    def test_validate_command_chaining_allowed_pipe(self):
        """Test that a command with a supported pipe command passes validation."""
        # Should not raise any exception
        try:
            self.policy.validate_command("show version | include V")
            self.assertTrue(True)  # No exception raised
        except Exception:
            self.fail("validate_command raised an exception unexpectedly!")


if __name__ == "__main__":
    unittest.main()
