"""Tests for the CommandSecurityPolicy class."""

import unittest
from src.security import CommandSecurityPolicy
from src.settings import settings


class TestCommandSecurityPolicy(unittest.TestCase):
    """Test cases for the CommandSecurityPolicy class."""

    def setUp(self):
        """Set up the test case."""
        self.policy = CommandSecurityPolicy()

    def test_validate_command_valid(self):
        """Test that a valid command passes validation."""
        is_valid, reason = self.policy.validate_command("show version")
        self.assertTrue(is_valid)
        self.assertEqual(reason, "")

    def test_validate_command_empty(self):
        """Test that an empty command fails validation."""
        is_valid, reason = self.policy.validate_command("")
        self.assertFalse(is_valid)
        self.assertEqual(reason, "Empty command")

    def test_validate_command_blocked_keyword(self):
        """Test that a command with a blocked keyword fails validation."""
        is_valid, reason = self.policy.validate_command("reload")
        self.assertFalse(is_valid)
        self.assertEqual(reason, "Blocked keyword 'reload'")

    def test_validate_command_not_allowed_prefix(self):
        """Test that a command with a not allowed prefix fails validation."""
        is_valid, reason = self.policy.validate_command("configure terminal")
        self.assertFalse(is_valid)
        self.assertEqual(reason, "Blocked keyword 'configure'")

    def test_validate_command_chaining_semicolon(self):
        """Test that a command with semicolon chaining fails validation."""
        is_valid, reason = self.policy.validate_command("show version; show ip interface brief")
        self.assertFalse(is_valid)
        self.assertEqual(reason, "Semicolon command chaining is not allowed")

    def test_validate_command_chaining_pipe(self):
        """Test that a command with an unsupported pipe command fails validation."""
        is_valid, reason = self.policy.validate_command("show version | grep test")
        self.assertFalse(is_valid)
        self.assertEqual(reason, "Unsupported pipe command")

    def test_validate_command_chaining_allowed_pipe(self):
        """Test that a command with a supported pipe command passes validation."""
        is_valid, reason = self.policy.validate_command("show version | include V")
        self.assertTrue(is_valid)
        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
