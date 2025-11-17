"""Core device router module."""

import re
from typing import Optional, Tuple

from .device_manager import DeviceManager
from .inventory import Device, InventoryManager


class DeviceRouter:
    """Routes queries to appropriate network devices."""

    def __init__(
        self, device_manager: DeviceManager, inventory_manager: InventoryManager
    ):
        self.device_manager = device_manager
        self.inventory_manager = inventory_manager

    def extract_device_reference(self, query: str) -> Tuple[Optional[Device], str]:
        """Extract device reference from query and return cleaned query."""
        # Look for device names in the query (e.g. "show version on R1", "R1 show interfaces")
        # Common patterns for device references in queries
        patterns = [
            r"on\s+(\w+)",  # "show version on R1"
            r"^(\w+)\s+",  # "R1 show version"
            r"(\w+)\s+.*show",  # "R1 show something"
            r"for\s+(\w+)",  # "show interfaces for R1"
        ]

        device_name = None
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                device_name = match.group(1)
                break

        if device_name:
            # Find the device in inventory
            device = self.inventory_manager.find_device_by_name(device_name)
            if device:
                # Remove device reference from query
                cleaned_query = re.sub(
                    rf"\b{device_name}\b", "", query, flags=re.IGNORECASE
                )
                cleaned_query = re.sub(
                    r"\s+", " ", cleaned_query
                ).strip()  # Clean up extra spaces
                cleaned_query = re.sub(
                    r"^on\s+|^for\s+", "", cleaned_query, flags=re.IGNORECASE
                ).strip()
                return device, cleaned_query

        # If no device reference found, try to infer from context or return first device
        devices = self.inventory_manager.list_devices()
        if devices:
            return devices[0], query  # Default to first device if none specified

        return None, query
