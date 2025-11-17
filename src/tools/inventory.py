"""Inventory tool for network devices."""

from langchain_core.tools import tool

from src.core.inventory import InventoryManager


inv = InventoryManager("inventory.yaml")


@tool
def inventory_search(query: str) -> str:
    """
    Search for devices or list all devices in the inventory.

    Use this tool when the user wants to:
    - List all available devices
    - Search for a specific device by name
    - Get information about devices

    Examples:
    - "list devices" → Returns all devices
    - "find D1" → Returns information about D1
    - "show me all switches" → Returns all devices

    Args:
        query: Natural language query about devices

    Returns:
        Device information in human-readable format
    """
    query_lower = query.lower()

    # Check if user wants to list all devices
    if any(keyword in query_lower for keyword in ["list", "all", "show devices"]):
        devices = inv.list_devices()
        if not devices:
            return "No devices found in inventory."

        result = "Available devices:\n"
        result += "\n".join(
            [
                f"  • {d.name} ({d.hostname}) - {d.device_type} - {d.description}"
                for d in devices
            ]
        )
        return result

    # Otherwise, search for specific device
    # Extract potential device name from query
    words = query.split()
    for word in words:
        dev = inv.find_device_by_name(word)
        if dev:
            return (
                f"Device: {dev.name}\n"
                f"Hostname: {dev.hostname}\n"
                f"Type: {dev.device_type}\n"
                f"Description: {dev.description}\n"
                f"Role: {dev.role}"
            )

    return f"No device found matching '{query}'. Available devices: " + ", ".join(
        [d.name for d in inv.list_devices()]
    )
