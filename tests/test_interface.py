"""Tests for the UserInterface class."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys
from src.interface import UserInterface, InputValidator
from src.audit import AuditLogger, SecurityEventType
from src.exceptions import QueryTooLongError, BlockedContentError


class TestInputValidator(unittest.TestCase):
    """Test cases for the InputValidator class."""

    def setUp(self):
        """Set up the test case."""
        self.mock_audit = Mock(spec=AuditLogger)
        self.validator = InputValidator(audit_logger=self.mock_audit, max_query_length=500)

    def test_validate_query_empty(self):
        """Test validating an empty query."""
        with self.assertRaises(BlockedContentError):
            self.validator.validate_query("")

        with self.assertRaises(BlockedContentError):
            self.validator.validate_query("   ")

    def test_validate_query_length_ok(self):
        """Test validating a query that is within length limits."""
        # Should not raise any exception
        try:
            self.validator.validate_query("This is a short query")
            self.assertTrue(True)  # No exception raised
        except Exception:
            self.fail("validate_query raised an exception unexpectedly!")

    def test_validate_query_too_long(self):
        """Test validating a query that exceeds length limits."""
        long_query = "a" * 600
        with self.assertRaises(QueryTooLongError):
            self.validator.validate_query(long_query)

    def test_validate_query_blocked_content(self):
        """Test validating a query with blocked content."""
        with self.assertRaises(BlockedContentError):
            self.validator.validate_query("reload system")

    def test_sanitize_query(self):
        """Test query sanitization."""
        raw_query = "  <script>test</script>   dangerous `code`   "
        sanitized = self.validator.sanitize_query(raw_query)
        # Should remove HTML tags, replace backticks, and trim whitespace
        self.assertNotIn("<script>", sanitized)
        self.assertNotIn("</script>", sanitized)
        self.assertNotIn("`", sanitized)
        self.assertEqual(sanitized, "test dangerous 'code'")

    def test_sanitize_query_null_bytes(self):
        """Test sanitizing query with null bytes."""
        raw_query = "test\x00query"
        sanitized = self.validator.sanitize_query(raw_query)
        self.assertNotIn("\x00", sanitized)
        self.assertEqual(sanitized, "testquery")


class TestUserInterface(unittest.TestCase):
    """Test cases for the UserInterface class."""

    def setUp(self):
        """Set up the test case."""
        # Mock the modules imported in interface.py to prevent actual execution
        self.mock_interface_module = Mock()

        # Patch all the imports for the interface module
        self.patches = [
            patch('src.interface.DeviceConnection'),
            patch('src.interface.Agent'),
            patch('src.interface.AuditLogger'),
            patch('src.interface.SensitiveDataProtector'),
            patch('src.interface.settings'),
            patch('src.interface.print_formatted_header'),
            patch('src.interface.print_line_separator'),
        ]

        self.mock_device_class = self.patches[0].start()
        self.mock_agent_class = self.patches[1].start()
        self.mock_audit_class = self.patches[2].start()
        self.mock_sensitive_class = self.patches[3].start()
        self.mock_settings = self.patches[4].start()
        self.mock_print_header = self.patches[5].start()
        self.mock_print_separator = self.patches[6].start()

        # Set up mock settings
        self.mock_settings.max_queries_per_session = 10
        self.mock_settings.max_query_length = 500
        self.mock_settings.groq_api_key = 'test_key'
        self.mock_settings.model_name = 'test-model'
        self.mock_settings.temperature = 0.1
        self.mock_settings.api_timeout = 60
        self.mock_settings.log_directory = 'logs'
        self.mock_settings.enable_console_logging = True
        self.mock_settings.enable_file_logging = True
        self.mock_settings.log_level = 'INFO'

        # Create mocks for device and agent
        self.mock_device = Mock()
        self.mock_agent = Mock()

        self.mock_device_class.return_value = self.mock_device
        self.mock_agent_class.return_value = self.mock_agent

    def tearDown(self):
        """Stop all patches."""
        for patch_obj in self.patches:
            patch_obj.stop()

    def test_initialization(self):
        """Test UserInterface initialization."""
        ui = UserInterface()

        # Check that audit logger and validator are created
        self.assertIsNotNone(ui.audit_logger)
        self.assertIsNotNone(ui.validator)
        self.assertEqual(ui.max_queries_per_session, 10)
        self.assertEqual(ui.query_count, 0)

    @patch('src.interface.getpass.getpass')
    @patch('builtins.input')
    def test_run_method_calls_components(self, mock_input, mock_getpass):
        """Test that run method calls the necessary components."""
        # Setup mock inputs
        mock_input.side_effect = [
            "192.168.1.1",  # hostname
            "admin",        # username
            "quit"          # question to quit
        ]
        mock_getpass.return_value = "password"

        ui = UserInterface()

        # Mock both the setup and connect methods to avoid actual connection attempts
        with patch.object(ui, '_setup_network_assistant') as mock_setup:
            # Make sure the device connection mock works
            ui.device = self.mock_device
            ui.assistant = self.mock_agent
            # Mock the connection to succeed
            ui.device.connect = Mock()
            # Mock the audit logger methods to succeed
            ui.audit_logger.log_connection_established = Mock()
            ui.audit_logger.log_session_start = Mock()

            with patch.object(ui, '_run_interactive_session') as mock_run:
                ui.run()

                # Assertions
                mock_input.assert_any_call("\nDevice IP: ")
                mock_input.assert_any_call("Username: ")
                mock_getpass.assert_called_once_with("Password: ")
                mock_setup.assert_called_once()
                # _run_interactive_session should now be called since connection succeeds
                mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()