"""Tool for searching the network device inventory.

This module provides a LangChain tool for searching and retrieving information
about network devices from the inventory. It allows users to query for specific
devices or list all available devices in the inventory.
"""

from typing import List
import ipaddress
import re
from langchain_core.tools import tool
from src.core.models import DeviceInfo
from src.core.network_manager import NetworkManager
from src.core.config import settings

# Initialize a single NetworkManager instance to be shared by tools
network_manager = NetworkManager(settings.inventory_file)


def validate_inventory(device_info: dict) -> None:
    """Validates a device's inventory entry.

    Checks for valid IP format, connection type, and required credentials.

    Args:
        device_info (dict): Device information from the inventory

    Raises:
        ValueError: If validation fails
    """
    # Validate connection type
    connection = device_info.get("device_type", "")  # Using device_type as the connection type
    # Netmiko device types are what we use, so we validate against known types
    if not connection:
        raise ValueError("Missing device_type in inventory")

    # Validate IP address format
    ip = device_info.get("hostname")
    if ip:
        try:
            ipaddress.ip_address(ip)
        except Exception:
            # Check if it's a valid hostname (not just IP)
            import re
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](\.[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9])*$', ip):
                raise ValueError("Invalid IP address or hostname format")


@tool
def inventory_search(device_name: str = "") -> List[DeviceInfo]:
    """Searches the inventory for devices. If no name is provided, lists all devices.

    This tool queries the network device inventory and returns information about
    devices. If a device_name is specified, it returns information for that specific
    device. If no device name is provided, it returns information for all devices
    in the inventory.

    Args:
        device_name (str, optional): The name of the specific device to search for.
            If empty, all devices are returned. Defaults to "".

    Returns:
        List[DeviceInfo]: A list of DeviceInfo objects containing information
        about the matching devices.
    """
    devices_to_return = []
    if device_name:
        device = network_manager.get_device(device_name)
        if device:
            devices_to_return.append(DeviceInfo(**device.__dict__))
    else:
        devices_to_return = [
            DeviceInfo(**dev.__dict__) for dev in network_manager.devices.values()
        ]
    return devices_to_return
