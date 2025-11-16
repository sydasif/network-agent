"""Unified registry for device inventory and active sessions."""

import logging
from typing import Dict, Optional, List

from .inventory import InventoryManager, InventoryDevice
from .network_device import DeviceConnection


logger = logging.getLogger("net_agent.devices")


class DeviceState:
    """Represents the state of a device - either inventory data or active session."""

    def __init__(self, device: InventoryDevice, session: Optional[DeviceConnection] = None):
        self.device = device  # Inventory entry (static data: hostname, username, etc.)
        self.session = session   # Active SSH connection session (None if not connected)
        self.is_connected = session is not None


class Registry:
    """Unified registry for managing device inventory and active connections."""
    
    def __init__(self, inventory_file: Optional[str] = None):
        """Initialize device registry."""
        self.inventory_manager = InventoryManager(inventory_file)
        self.sessions: Dict[str, DeviceConnection] = {}  # active connections
        self.current_device_name: Optional[str] = None
    
    @property
    def devices(self) -> Dict[str, DeviceState]:
        """Get all devices with their state (inventory + connection)."""
        device_states = {}
        for name, inventory_device in self.inventory_manager.devices.items():
            session = self.sessions.get(name)
            device_states[name] = DeviceState(inventory_device, session)
        return device_states
    
    def connect(self, device_name: str) -> bool:
        """Connect to a device."""
        if device_name not in self.inventory_manager.devices:
            logger.warning(f"Device '{device_name}' not found in inventory")
            return False
        
        if device_name in self.sessions:
            # Already connected
            self.current_device_name = device_name
            return True
        
        try:
            device_info = self.inventory_manager.get_device(device_name)
            if not device_info:
                return False
            
            # Create new connection
            connection = DeviceConnection()
            connection.connect(
                hostname=device_info.hostname,
                username=device_info.username,
                password=device_info.password,
            )

            # Store the connection
            self.sessions[device_name] = connection
            self.current_device_name = device_name

            logger.info(f"Connected to device: {device_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {device_name}: {e}")
            return False
    
    def disconnect(self, device_name: str) -> bool:
        """Disconnect from a device."""
        if device_name not in self.sessions:
            return False

        connection = self.sessions[device_name]
        try:
            connection.disconnect()
            del self.sessions[device_name]

            # If we disconnected the current device, reset current device
            if self.current_device_name == device_name:
                if self.sessions:
                    # Switch to another connected device if available
                    self.current_device_name = next(iter(self.sessions))
                else:
                    self.current_device_name = None

            logger.info(f"Disconnected from device: {device_name}")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting from {device_name}: {e}")
            return False
    
    def switch(self, device_name: str) -> bool:
        """Switch to a different connected device."""
        if device_name not in self.sessions:
            raise ValueError(f"Device {device_name} not connected")

        self.current_device_name = device_name
        logger.info(f"Switched to device: {device_name}")
        return True
    
    def get_current_name(self) -> Optional[str]:
        """Get the name of the currently selected device."""
        return self.current_device_name
    
    def get_current_session(self) -> Optional[DeviceConnection]:
        """Get the current device session."""
        if self.current_device_name and self.current_device_name in self.sessions:
            return self.sessions[self.current_device_name]
        return None

    def execute_on_current_session(self, command: str) -> str:
        """Execute a command on the current active session."""
        session = self.get_current_session()
        if not session:
            return "❌ No active device session. Please connect to a device first."
        return session.execute_command(command)
    
    def get_connected(self) -> Dict[str, DeviceConnection]:
        """Get all connected devices."""
        return self.sessions.copy()
    
    def is_connected(self, device_name: str) -> bool:
        """Check if a device is connected."""
        return device_name in self.sessions
    
    def disconnect_all(self) -> None:
        """Disconnect from all devices."""
        for device_name in list(self.sessions.keys()):
            try:
                self.disconnect(device_name)
            except Exception as e:
                logger.error(f"Error disconnecting from {device_name}: {e}")

        self.current_device_name = None
        logger.info("Disconnected from all devices")
    
    def get_device(self, name: str) -> Optional[InventoryDevice]:
        """Get device from inventory by name."""
        return self.inventory_manager.get_device(name)
    
    def list_devices(self) -> List[InventoryDevice]:
        """List all devices in inventory."""
        return self.inventory_manager.list_devices()
    
    def __len__(self) -> int:
        """Return number of devices in inventory."""
        return len(self.inventory_manager)
    
    def __contains__(self, name: str) -> bool:
        """Check if device exists in inventory."""
        return name in self.inventory_manager