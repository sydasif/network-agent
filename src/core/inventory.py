"""Core inventory management module."""

from dataclasses import dataclass
from typing import List, Optional

import yaml


@dataclass
class Device:
    """Device dataclass to represent network devices."""

    name: str
    hostname: str
    username: str
    password: str
    device_type: str
    description: str = ""
    role: str = ""


class InventoryManager:
    """Manages the inventory of network devices."""

    def __init__(self, inventory_file: str):
        self.inventory_file = inventory_file
        self.devices = self._load_inventory()

    def _load_inventory(self) -> List[Device]:
        """Load inventory from YAML file."""
        try:
            with open(self.inventory_file, "r") as f:
                data = yaml.safe_load(f)

            devices = []
            for device_data in data.get("devices", []):
                device = Device(
                    name=device_data["name"],
                    hostname=device_data["hostname"],
                    username=device_data["username"],
                    password=device_data["password"],
                    device_type=device_data["device_type"],
                    description=device_data.get("description", ""),
                    role=device_data.get("role", ""),
                )
                devices.append(device)

            return devices
        except Exception as e:
            print(f"Error loading inventory: {e}")
            return []

    def list_devices(self) -> List[Device]:
        """Return all devices in the inventory."""
        return self.devices

    def find_device_by_name(self, name: str) -> Optional[Device]:
        """Find a device by its name."""
        for device in self.devices:
            if device.name.lower() == name.lower():
                return device
        return None
