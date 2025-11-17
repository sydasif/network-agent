"""Inventory tool for network devices."""

from typing import Optional

from langchain_core.tools import tool

from src.core.network_manager import NetworkManager


network_manager = NetworkManager("inventory.yaml")


@tool
def inventory_search(device_name: Optional[str] = None) -> str:
    """
    Search for devices or list all devices in the inventory.

    Use this tool when the user wants to:
    - List all available devices
    - Search for a specific device by name
    - Get information about devices

    Args:
        device_name: Name of specific device to search for (optional, if None returns all devices)

    Returns:
        Device information in human-readable format
    """
    if device_name:
        # Search for specific device
        device = network_manager.get_device(device_name)
        if device:
            return (
                f"Device: {device.name}\n"
                f"Hostname: {device.hostname}\n"
                f"Type: {device.device_type}\n"
                f"Description: {device.description}\n"
                f"Role: {device.role}"
            )
        available_devices = list(network_manager.devices.keys())
        return f"Device '{device_name}' not found. Available devices: {', '.join(available_devices) if available_devices else 'None'}"
    # List all devices
    if not network_manager.devices:
        return "No devices found in inventory."

    result = "Available devices:\n"
    result += "\n".join(
        [
            f"  • {d.name} ({d.hostname}) - {d.device_type} - {d.description}"
            for d in network_manager.devices.values()
        ]
    )
    return result
