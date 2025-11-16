"""Multi-device connection management."""

import logging
from typing import Dict, Optional

from .inventory import InventoryDevice
from .network_device import DeviceConnection


logger = logging.getLogger("net_agent.device_manager")


class DeviceManager:
    """Manage multiple device connections."""

    def __init__(self):
        """Initialize device manager."""
        self.devices: Dict[str, DeviceConnection] = {}
        self.current_device_name: Optional[str] = None
        self.connections: Dict[str, DeviceConnection] = {}

    def connect_to_device(self, device_name: str, device_info: InventoryDevice) -> bool:
        """Connect to a device.

        Args:
            device_name: Name of the device
            device_info: InventoryDevice information

        Returns:
            True if connection successful
        """
        if device_name in self.connections:
            # Already connected
            self.current_device_name = device_name
            return True

        try:
            # Create new connection
            connection = DeviceConnection()
            connection.connect(
                hostname=device_info.hostname,
                username=device_info.username,
                password=device_info.password,
            )

            # Store the connection
            self.connections[device_name] = connection
            self.current_device_name = device_name

            logger.info(f"Connected to device: {device_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {device_name}: {e}")
            return False

    def disconnect_from_device(self, device_name: str) -> bool:
        """Disconnect from a device.

        Args:
            device_name: Name of the device to disconnect

        Returns:
            True if disconnected successfully
        """
        if device_name not in self.connections:
            return False

        connection = self.connections[device_name]
        try:
            connection.disconnect()
            del self.connections[device_name]

            # If we disconnected the current device, reset current device
            if self.current_device_name == device_name:
                if self.connections:
                    # Switch to another connected device if available
                    self.current_device_name = next(iter(self.connections))
                else:
                    self.current_device_name = None

            logger.info(f"Disconnected from device: {device_name}")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting from {device_name}: {e}")
            return False

    def switch_device(self, device_name: str) -> bool:
        """Switch to a different connected device.

        Args:
            device_name: Name of the device to switch to

        Returns:
            True if switch successful
        """
        if device_name not in self.connections:
            raise ValueError(f"Device {device_name} not connected")

        self.current_device_name = device_name
        logger.info(f"Switched to device: {device_name}")
        return True

    def get_current_device_name(self) -> Optional[str]:
        """Get the name of the currently selected device.

        Returns:
            Current device name or None
        """
        return self.current_device_name

    def get_current_connection(self) -> Optional[DeviceConnection]:
        """Get the current device connection.

        Returns:
            Current connection or None
        """
        if self.current_device_name and self.current_device_name in self.connections:
            return self.connections[self.current_device_name]
        return None

    def get_connected_devices(self) -> Dict[str, DeviceConnection]:
        """Get all connected devices.

        Returns:
            Dictionary of connected devices
        """
        return self.connections.copy()

    def is_connected(self, device_name: str) -> bool:
        """Check if a device is connected.

        Args:
            device_name: Name of the device to check

        Returns:
            True if device is connected
        """
        return device_name in self.connections

    def disconnect_all(self) -> None:
        """Disconnect from all devices."""
        for device_name in list(self.connections.keys()):
            try:
                self.disconnect_from_device(device_name)
            except Exception as e:
                logger.error(f"Error disconnecting from {device_name}: {e}")

        self.current_device_name = None
        logger.info("Disconnected from all devices")

    def __contains__(self, device_name: str) -> bool:
        """Check if a device is connected."""
        return device_name in self.connections
