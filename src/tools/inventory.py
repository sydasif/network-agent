"""Inventory tool for network devices."""

from langchain_core.tools import tool

from src.core.inventory import InventoryManager


inv = InventoryManager("inventory.yaml")


@tool
def inventory_search(query: str) -> str:
    """
    Search devices or list all devices.
    """
    if "list" in query.lower():
        devices = inv.list_devices()
        return "\n".join([f"{d.name} - {d.hostname}" for d in devices])

    dev = inv.find_device_by_name(query)
    if not dev:
        return "No device found."

    return f"Name: {dev.name}\nIP: {dev.hostname}\nType: {dev.device_type}"
