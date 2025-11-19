"""Tests for the NetworkManager class."""

from unittest.mock import patch, mock_open
from src.core.network_manager import NetworkManager, Device


class TestNetworkManager:
    """Test suite for NetworkManager class."""

    def test_initialization_with_custom_inventory_file(self):
        """Test NetworkManager initialization with custom inventory file."""
        custom_file = "custom_inventory.yaml"
        with patch("src.core.config.settings") as mock_settings:
            mock_settings.inventory_file = "default_inventory.yaml"
            network_manager = NetworkManager(inventory_file=custom_file)
            assert network_manager.inventory_file == custom_file

    def test_initialization_with_default_inventory_file(self):
        """Test NetworkManager initialization with default inventory file."""
        default_file = "default_inventory.yaml"
        with patch("src.core.config.settings") as mock_settings:
            mock_settings.inventory_file = default_file
            network_manager = NetworkManager()
            assert network_manager.inventory_file == default_file

    def test_get_device_existing_device(self):
        """Test getting an existing device."""
        network_manager = NetworkManager()
        # Manually populate the devices dictionary for testing
        test_device = Device(
            name="test_device",
            hostname="192.168.1.1",
            username="admin",
            password="password",
            device_type="cisco_ios",
        )
        network_manager.devices = {"test_device": test_device}

        retrieved_device = network_manager.get_device("test_device")
        assert retrieved_device is not None
        assert retrieved_device.name == "test_device"

    def test_get_device_non_existing_device(self):
        """Test getting a non-existing device."""
        network_manager = NetworkManager()
        network_manager.devices = {}

        retrieved_device = network_manager.get_device("non_existing")
        assert retrieved_device is None

    @patch("builtins.open", new_callable=mock_open, read_data='{"devices": []}')
    @patch("yaml.safe_load")
    def test_load_inventory_empty(self, mock_yaml_load, mock_file):
        """Test loading an empty inventory."""
        mock_yaml_load.return_value = {"devices": []}
        network_manager = NetworkManager()

        devices = network_manager._load_inventory()
        assert devices == {}

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"devices": [{"name": "device1", "hostname": "192.168.1.1", "username": "admin", "password": "password", "device_type": "cisco_ios"}]}',
    )
    @patch("yaml.safe_load")
    def test_load_inventory_with_devices(self, mock_yaml_load, mock_file):
        """Test loading inventory with devices."""
        mock_yaml_load.return_value = {
            "devices": [
                {
                    "name": "device1",
                    "hostname": "192.168.1.1",
                    "username": "admin",
                    "password": "password",
                    "device_type": "cisco_ios",
                }
            ]
        }
        network_manager = NetworkManager()

        devices = network_manager._load_inventory()
        assert len(devices) == 1
        assert "device1" in devices
        assert devices["device1"].name == "device1"
        assert devices["device1"].hostname == "192.168.1.1"


    def test_is_dangerous_command_safe_command(self):
        """Test identifying safe commands."""
        network_manager = NetworkManager()

        safe_command = "show version"
        assert not network_manager._is_dangerous_command(safe_command)

    def test_is_dangerous_command_dangerous_command(self):
        """Test identifying dangerous commands."""
        network_manager = NetworkManager()

        dangerous_command = "write erase"
        assert network_manager._is_dangerous_command(dangerous_command)

    def test_sanitize_output_removes_passwords(self):
        """Test that sensitive information is redacted from output."""
        network_manager = NetworkManager()

        output_with_password = "username admin password 12345 secret 67890"
        sanitized_output = network_manager._sanitize_output(output_with_password)

        assert "[REDACTED]" in sanitized_output
        assert "12345" not in sanitized_output
        assert "67890" not in sanitized_output
