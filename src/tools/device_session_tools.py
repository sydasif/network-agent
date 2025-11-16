"""LangChain tools for managing device connections."""

import logging
from typing import Optional
from langchain_core.tools import tool

from ..device_manager import DeviceManager
from ..inventory import InventoryManager, InventoryDevice


logger = logging.getLogger("net_agent.tools.device_session_tools")


class DeviceSessionTools:
    """Class to create LangChain tools for device session management."""
    
    def __init__(self, device_manager: DeviceManager, inventory_manager: InventoryManager):
        self.device_manager = device_manager
        self.inventory_manager = inventory_manager

    def create_connect_device_tool(self):
        """Create the connect_device tool."""
        
        @tool
        def connect_device(device_name: str) -> str:
            """
            Connect to a device by name from the inventory.
            
            Args:
                device_name: Name of the device to connect to
                
            Returns:
                str: Connection status message
            """
            # Check if device exists in inventory
            device_info = self.inventory_manager.get_device(device_name)
            if not device_info:
                return f"❌ Device '{device_name}' not found in inventory."
            
            # Try to connect to the device
            try:
                success = self.device_manager.connect_to_device(device_name, device_info)
                if success:
                    return f"✓ Successfully connected to {device_name} ({device_info.hostname})"
                else:
                    return f"❌ Failed to connect to {device_name}"
            except Exception as e:
                logger.error(f"Error connecting to {device_name}: {e}")
                return f"❌ Error connecting to {device_name}: {str(e)}"

        return connect_device

    def create_switch_device_tool(self):
        """Create the switch_device tool."""
        
        @tool
        def switch_device(device_name: str) -> str:
            """
            Switch to a different connected device.
            
            Args:
                device_name: Name of the device to switch to
                
            Returns:
                str: Switch status message
            """
            if device_name not in self.device_manager:
                return f"❌ Device '{device_name}' is not connected."
                
            try:
                success = self.device_manager.switch_device(device_name)
                if success:
                    return f"✓ Switched to device {device_name}"
                else:
                    return f"❌ Failed to switch to {device_name}"
            except ValueError as e:
                return f"❌ Error switching to {device_name}: {str(e)}"
            except Exception as e:
                logger.error(f"Error switching to {device_name}: {e}")
                return f"❌ Error switching to {device_name}: {str(e)}"

        return switch_device

    def create_disconnect_device_tool(self):
        """Create the disconnect_device tool."""
        
        @tool
        def disconnect_device(device_name: str) -> str:
            """
            Disconnect from a device.
            
            Args:
                device_name: Name of the device to disconnect from
                
            Returns:
                str: Disconnect status message
            """
            if device_name not in self.device_manager:
                return f"❌ Device '{device_name}' is not connected."
                
            try:
                success = self.device_manager.disconnect_from_device(device_name)
                if success:
                    return f"✓ Disconnected from {device_name}"
                else:
                    return f"❌ Failed to disconnect from {device_name}"
            except Exception as e:
                logger.error(f"Error disconnecting from {device_name}: {e}")
                return f"❌ Error disconnecting from {device_name}: {str(e)}"

        return disconnect_device

    def create_get_current_device_tool(self):
        """Create the get_current_device tool."""
        
        @tool
        def get_current_device() -> str:
            """
            Get the name of the currently selected device.
            
            Returns:
                str: Current device name or None if no device is selected
            """
            current_device = self.device_manager.get_current_device_name()
            if current_device:
                return f"Currently connected to: {current_device}"
            else:
                return "No device currently selected"

        return get_current_device