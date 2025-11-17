"""Tool for searching the network device inventory."""

from typing import List
from langchain_core.tools import tool
from src.core.models import DeviceInfo
from src.core.manager import NetworkManager
from src.core.config import settings

# Initialize a single NetworkManager instance to be shared by tools
network_manager = NetworkManager(settings.inventory_file)


@tool
def inventory_search(device_name: str = "") -> List[DeviceInfo]:
    """
    Searches the inventory for devices. If no name is provided, lists all devices.
    Use this to find device names, roles, or hostnames.
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
