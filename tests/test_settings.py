"""Tests for the Settings class."""

import unittest
import os
from unittest.mock import patch
from src.settings import Settings


class TestSettings(unittest.TestCase):
    """Test cases for the Settings class."""

    def setUp(self):
        """Set up the test case."""
        # Clear environment variables that might interfere with tests
        if 'GROQ_API_KEY' in os.environ:
            del os.environ['GROQ_API_KEY']

    @patch.dict(os.environ, {
        'GROQ_API_KEY': 'test_key',
        'MODEL_NAME': 'test-model',
        'MAX_QUERY_LENGTH': '1000'
    })
    def test_settings_from_environment(self):
        """Test loading settings from environment variables."""
        settings = Settings()
        self.assertEqual(settings.model_name, 'test-model')
        self.assertEqual(settings.max_query_length, 1000)
        self.assertEqual(settings.groq_api_key, 'test_key')

    def test_settings_default_values(self):
        """Test default values for settings."""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            settings = Settings()
            self.assertEqual(settings.model_name, 'llama-3.3-70b-versatile')
            self.assertEqual(settings.temperature, 0.1)
            self.assertEqual(settings.api_timeout, 60)
            self.assertEqual(settings.max_query_length, 500)
            self.assertEqual(settings.log_level, 'INFO')
            self.assertEqual(settings.connection_timeout, 30)
            self.assertEqual(settings.groq_api_key, 'test_key')

    def test_settings_allowed_commands(self):
        """Test allowed commands setting."""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            settings = Settings()
            expected_commands = ["show", "display", "get", "dir", "more", "verify"]
            self.assertEqual(settings.allowed_commands, expected_commands)

    def test_settings_blocked_keywords(self):
        """Test blocked keywords setting."""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            settings = Settings()
            expected_keywords = [
                "reload", "write", "erase", "delete", "no", "clear", "configure",
                "conf", "enable", "copy", "format", "shutdown", "boot",
                "username", "password", "crypto", "key", "certificate"
            ]
            self.assertEqual(settings.blocked_keywords, expected_keywords)

    def test_settings_validation(self):
        """Test settings validation."""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            settings = Settings()
            # Should not raise an exception for valid settings
            self.assertIsInstance(settings, Settings)


if __name__ == "__main__":
    unittest.main()