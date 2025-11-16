"""Tests for the DeviceConnection class."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.network_device import DeviceConnection, ConnectionState


class TestDeviceConnection(unittest.TestCase):
    """Test cases for the DeviceConnection class."""

    def setUp(self):
        """Set up the test case."""
        self.device = DeviceConnection()

    def test_initial_state(self):
        """Test initial connection state."""
        self.assertIsNone(self.device.connection)
        self.assertEqual(self.device.state, ConnectionState.DISCONNECTED)
        self.assertIsNone(self.device.device_config)
        self.assertIsNone(self.device.last_error)

    @patch('src.network_device.ConnectHandler')
    def test_connect_success(self, mock_connect_handler):
        """Test successful connection."""
        mock_connection = Mock()
        mock_connect_handler.return_value = mock_connection

        self.device.connect("192.168.1.1", "admin", "password")

        mock_connect_handler.assert_called_once()
        self.assertEqual(self.device.state, ConnectionState.CONNECTED)
        self.assertIsNotNone(self.device.connection)
        self.assertIsNone(self.device.last_error)

    @patch('src.network_device.ConnectHandler')
    def test_connect_authentication_failure(self, mock_connect_handler):
        """Test connection failure due to authentication."""
        from netmiko.exceptions import NetmikoAuthenticationException
        mock_connect_handler.side_effect = NetmikoAuthenticationException("Auth failed")

        with self.assertRaises(ConnectionError) as context:
            self.device.connect("192.168.1.1", "admin", "password")

        self.assertEqual(self.device.state, ConnectionState.FAILED)
        self.assertEqual(self.device.last_error, "Authentication failed")
        self.assertIn("SSH Authentication Failed", str(context.exception))

    @patch('src.network_device.ConnectHandler')
    def test_connect_timeout_failure(self, mock_connect_handler):
        """Test connection failure due to timeout."""
        from netmiko.exceptions import NetmikoTimeoutException
        mock_connect_handler.side_effect = NetmikoTimeoutException("Timeout")

        with self.assertRaises(ConnectionError) as context:
            self.device.connect("192.168.1.1", "admin", "password")

        self.assertEqual(self.device.state, ConnectionState.FAILED)
        self.assertEqual(self.device.last_error, "Connection timeout after retries")
        self.assertIn("Connection Timeout", str(context.exception))

    @patch('src.network_device.ConnectHandler')
    def test_disconnect(self, mock_connect_handler):
        """Test disconnect functionality."""
        mock_connection = Mock()
        mock_connect_handler.return_value = mock_connection
        self.device.connection = mock_connection

        self.device.disconnect()

        mock_connection.disconnect.assert_called_once()
        self.assertIsNone(self.device.connection)
        self.assertEqual(self.device.state, ConnectionState.DISCONNECTED)

    @patch('src.network_device.ConnectHandler')
    def test_execute_command_success(self, mock_connect_handler):
        """Test successful command execution."""
        mock_connection = Mock()
        mock_connection.is_alive.return_value = True
        mock_connect_handler.return_value = mock_connection
        mock_connection.send_command.return_value = "Command output"

        self.device.connection = mock_connection

        result = self.device.execute_command("show version")

        mock_connection.send_command.assert_called_once_with(
            "show version",
            read_timeout=60,  # Default command_timeout
            expect_string=r"#"
        )
        self.assertEqual(result, "Command output")

    @patch('src.network_device.ConnectHandler')
    def test_execute_command_connection_dead(self, mock_connect_handler):
        """Test command execution when connection is dead."""
        mock_connection = Mock()
        mock_connection.is_alive.return_value = False
        mock_connect_handler.return_value = mock_connection
        self.device.connection = mock_connection

        with self.assertRaises(ConnectionError) as context:
            self.device.execute_command("show version")

        self.assertEqual(self.device.state, ConnectionState.FAILED)
        self.assertIn("Not connected to device", str(context.exception))

    @patch('src.network_device.ConnectHandler')
    def test_execute_command_timeout(self, mock_connect_handler):
        """Test command execution timeout."""
        from netmiko.exceptions import NetmikoTimeoutException
        mock_connection = Mock()
        mock_connection.is_alive.return_value = True
        mock_connect_handler.return_value = mock_connection
        mock_connection.send_command.side_effect = NetmikoTimeoutException("Command timeout")
        self.device.connection = mock_connection

        with self.assertRaises(ConnectionError) as context:
            self.device.execute_command("show version")

        self.assertEqual(self.device.state, ConnectionState.FAILED)
        self.assertIn("Command execution timeout", str(context.exception))

    def test_get_connection_status_disconnected(self):
        """Test connection status when disconnected."""
        status = self.device.get_connection_status()

        self.assertEqual(status['state'], ConnectionState.DISCONNECTED)
        self.assertFalse(status['connected'])
        self.assertFalse(status['is_alive'])
        self.assertIsNone(status['device'])
        self.assertIsNone(status['last_error'])

    @patch('src.network_device.ConnectHandler')
    def test_get_connection_status_connected(self, mock_connect_handler):
        """Test connection status when connected."""
        mock_connection = Mock()
        mock_connection.is_alive.return_value = True
        mock_connect_handler.return_value = mock_connection
        self.device.connection = mock_connection
        self.device.state = ConnectionState.CONNECTED
        self.device.device_config = {"host": "192.168.1.1"}

        status = self.device.get_connection_status()

        self.assertEqual(status['state'], ConnectionState.CONNECTED)
        self.assertTrue(status['connected'])
        self.assertTrue(status['is_alive'])
        self.assertEqual(status['device'], "192.168.1.1")


if __name__ == "__main__":
    unittest.main()