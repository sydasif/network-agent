"""LangChain tools for inventory management."""

import logging
from typing import List
from langchain_core.tools import tool

from ..inventory import InventoryManager


logger = logging.getLogger("net_agent.tools.inventory_tools")


class InventoryTools:
    """Class to create LangChain tools for inventory management."""
    
    def __init__(self, inventory_manager: InventoryManager):
        self.inventory_manager = inventory_manager

    def create_get_inventory_tool(self):
        """Create the get_inventory tool."""
        
        @tool
        def get_inventory() -> str:
            """
            Get a list of all devices in the inventory.
            
            Returns:
                str: Formatted list of devices with their details
            """
            devices = self.inventory_manager.list_devices()
            
            if not devices:
                return "No devices in inventory."
            
            result = f"Found {len(devices)} device(s) in inventory:\n"
            for device in devices:
                result += f"  - {device.name} ({device.hostname}) [{device.role or 'N/A'}] - {device.description or 'No description'}\n"
            
            return result

        return get_inventory

    def create_search_inventory_tool(self):
        """Create the search_inventory tool."""
        
        @tool
        def search_inventory(query: str) -> str:
            """
            Search devices in the inventory by name, hostname, description, or location.
            
            Args:
                query: Search query string
                
            Returns:
                str: Formatted list of matching devices
            """
            results = self.inventory_manager.search_devices(query)
            
            if not results:
                return f"No devices found matching '{query}'."
            
            result = f"Found {len(results)} device(s) matching '{query}':\n"
            for device in results:
                result += f"  - {device.name} ({device.hostname}) [{device.role or 'N/A'}] - {device.description or 'No description'}\n"
            
            return result

        return search_inventory

    def create_get_device_info_tool(self):
        """Create the get_device_info tool."""
        
        @tool
        def get_device_info(device_name: str) -> str:
            """
            Get detailed information about a specific device.
            
            Args:
                device_name: Name of the device to get info for
                
            Returns:
                str: Detailed device information
            """
            device = self.inventory_manager.get_device(device_name)
            
            if not device:
                return f"Device '{device_name}' not found in inventory."
            
            info = f"Device: {device.name}\n"
            info += f"Hostname: {device.hostname}\n"
            info += f"Device Type: {device.device_type}\n"
            info += f"Port: {device.port}\n"
            info += f"Username: {device.username}\n"
            info += f"Role: {device.role or 'N/A'}\n"
            info += f"Location: {device.location or 'N/A'}\n"
            info += f"Description: {device.description or 'N/A'}\n"
            
            return info

        return get_device_info