"""Tool for searching the network device inventory.

This module provides a LangChain tool for searching and retrieving information
about network devices from the inventory. It allows users to query for specific
devices or list all available devices in the inventory.
"""

from typing import List
from langchain_core.tools import tool
from src.core.models import DeviceInfo
from src.core.network_manager import NetworkManager
from src.core.config import settings

# Initialize a single NetworkManager instance to be shared by tools
network_manager = NetworkManager(settings.inventory_file)




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
