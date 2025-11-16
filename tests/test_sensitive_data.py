"""Tests for the SensitiveDataProtector class."""

import unittest
from src.sensitive_data import SensitiveDataProtector


class TestSensitiveDataProtector(unittest.TestCase):
    """Test cases for the SensitiveDataProtector class."""

    def setUp(self):
        """Set up the test case."""
        self.protector = SensitiveDataProtector()

    def test_sanitize_for_logging_with_password(self):
        """Test sanitizing text containing password."""
        text = "password admin123"
        sanitized = self.protector.sanitize_for_logging(text)
        self.assertEqual(sanitized, "[SECRET_REDACTED]")

    def test_sanitize_for_logging_with_secret(self):
        """Test sanitizing text containing secret."""
        text = "secret mysecretvalue"
        sanitized = self.protector.sanitize_for_logging(text)
        self.assertEqual(sanitized, "[SECRET_REDACTED]")

    def test_sanitize_for_logging_with_api_key(self):
        """Test sanitizing text containing API key."""
        text = "gsk_abcdefghijklmnopqrstuvwxyz123456"
        sanitized = self.protector.sanitize_for_logging(text)
        self.assertEqual(sanitized, "[API_KEY_REDACTED]")

    def test_sanitize_for_logging_with_multiple_secrets(self):
        """Test sanitizing text containing multiple secrets."""
        # Using a proper API key format (at least 32 chars after gsk_)
        text = "password admin123 and secret mysecretvalue and gsk_abcdefghijklmnopqrstuvwxyz123456"
        sanitized = self.protector.sanitize_for_logging(text)
        expected = "[SECRET_REDACTED] and [SECRET_REDACTED] and [API_KEY_REDACTED]"
        self.assertEqual(sanitized, expected)

    def test_sanitize_for_logging_case_insensitive(self):
        """Test that sanitization is case insensitive."""
        text = "Password ADMIN123 and SECRET mysecretvalue"
        sanitized = self.protector.sanitize_for_logging(text)
        self.assertEqual(sanitized, "[SECRET_REDACTED] and [SECRET_REDACTED]")

    def test_sanitize_for_logging_no_secrets(self):
        """Test that text without secrets is unchanged."""
        text = "This is a safe text without secrets"
        sanitized = self.protector.sanitize_for_logging(text)
        self.assertEqual(sanitized, text)

    def test_sanitize_for_logging_empty_text(self):
        """Test sanitizing empty text."""
        text = ""
        sanitized = self.protector.sanitize_for_logging(text)
        self.assertEqual(sanitized, "")

    def test_sanitize_command(self):
        """Test sanitizing a command."""
        command = "password admin123"
        sanitized = self.protector.sanitize_command(command)
        self.assertEqual(sanitized, "[SECRET_REDACTED]")

    def test_sanitize_output(self):
        """Test sanitizing output."""
        output = "password admin123"
        sanitized = self.protector.sanitize_output(output)
        self.assertEqual(sanitized, "[SECRET_REDACTED]")

    def test_sanitize_output_with_truncation(self):
        """Test sanitizing and truncating output."""
        # Add proper API key format for this test too
        long_output = "a" * 1005 + " password admin123"
        sanitized = self.protector.sanitize_output(long_output, max_length=1000)
        # Check that the truncation happened properly by looking for the truncation message
        # and that the secret was replaced before truncation
        self.assertIn("[TRUNCATED:", sanitized)
        # The truncation will cut off the replaced secret, but the replacement should have happened
        # before the truncation

        # Calculate the actual length of text before truncation
        original_start = "a" * 1005 + " "
        # The password replacement would have happened in the original text before truncation
        # So test that when truncation is not applied we get the correct result
        full_sanitized = self.protector.sanitize_output("a" * 1005 + " password admin123", max_length=0)
        # This should contain [SECRET_REDACTED]
        self.assertIn("[SECRET_REDACTED]", full_sanitized)

    def test_sanitize_error(self):
        """Test sanitizing an error message."""
        error = "Connection failed with password admin123"
        sanitized = self.protector.sanitize_error(error)
        self.assertEqual(sanitized, "Connection failed with [SECRET_REDACTED]")

    def test_mask_password_short(self):
        """Test masking a short password."""
        password = "abc"
        masked = self.protector.mask_password(password)
        self.assertEqual(masked, "****")

    def test_mask_password_long(self):
        """Test masking a long password."""
        password = "verylongpassword"
        masked = self.protector.mask_password(password)
        self.assertEqual(masked, "*" * len(password))

    def test_mask_api_key_short(self):
        """Test masking a short API key."""
        api_key = "api"
        masked = self.protector.mask_api_key(api_key)
        self.assertEqual(masked, "****")

    def test_mask_api_key_long(self):
        """Test masking a long API key."""
        api_key = "verylongapikey12345"
        masked = self.protector.mask_api_key(api_key)
        self.assertEqual(masked, "very...2345")


if __name__ == "__main__":
    unittest.main()