"""Device inventory management from YAML/JSON files."""

import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from .exceptions import NetworkAgentError


logger = logging.getLogger("net_agent.inventory")


@dataclass
class InventoryDevice:
    """Device information from inventory."""

    name: str
    hostname: str
    username: str
    password: str
    device_type: str = "cisco_ios"
    port: int = 22
    description: Optional[str] = None
    location: Optional[str] = None
    role: Optional[str] = None  # e.g., "core", "edge", "access"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class InventoryManager:
    """Manage device inventory from files."""

    def __init__(self, inventory_file: Optional[str] = None):
        """Initialize inventory manager.

        Args:
            inventory_file: Path to inventory file (YAML or JSON)
        """
        self.devices: Dict[str, InventoryDevice] = {}
        self.inventory_file = inventory_file

        if inventory_file:
            self.load_from_file(inventory_file)

    def load_from_file(self, file_path: str):
        """Load inventory from YAML or JSON file.

        Args:
            file_path: Path to inventory file

        Raises:
            NetworkAgentError: If file cannot be loaded
        """
        path = Path(file_path)

        if not path.exists():
            raise NetworkAgentError(f"Inventory file not found: {file_path}")

        try:
            with open(path, "r") as f:
                if path.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif path.suffix == ".json":
                    data = json.load(f)
                else:
                    raise NetworkAgentError(
                        f"Unsupported inventory format: {path.suffix}. "
                        f"Use .yaml, .yml, or .json"
                    )

            self._parse_inventory(data)
            logger.info(f"Loaded {len(self.devices)} devices from {file_path}")

        except Exception as e:
            raise NetworkAgentError(f"Failed to load inventory: {e}") from e

    def _parse_inventory(self, data: dict):
        """Parse inventory data structure.

        Expected format:
        {
            "devices": [
                {
                    "name": "router1",
                    "hostname": "192.168.1.1",
                    "username": "admin",
                    "password": "secret",
                    "description": "Core Router",
                    "role": "core"
                },
                ...
            ]
        }
        """
        if "devices" not in data:
            raise NetworkAgentError(
                "Invalid inventory format. Expected 'devices' key at root level."
            )

        devices_list = data["devices"]

        for device_data in devices_list:
            # Validate required fields
            required = ["name", "hostname", "username", "password"]
            missing = [f for f in required if f not in device_data]

            if missing:
                logger.warning(
                    f"Skipping device - missing fields: {', '.join(missing)}"
                )
                continue

            device = InventoryDevice(
                name=device_data["name"],
                hostname=device_data["hostname"],
                username=device_data["username"],
                password=device_data["password"],
                device_type=device_data.get("device_type", "cisco_ios"),
                port=device_data.get("port", 22),
                description=device_data.get("description"),
                location=device_data.get("location"),
                role=device_data.get("role"),
            )

            self.devices[device.name] = device

    def get_device(self, name: str) -> Optional[InventoryDevice]:
        """Get device by name (case-insensitive).

        Args:
            name: Device name

        Returns:
            InventoryDevice or None
        """
        # Try exact match first
        if name in self.devices:
            return self.devices[name]

        # Try case-insensitive match
        name_lower = name.lower()
        for device_name, device in self.devices.items():
            if device_name.lower() == name_lower:
                return device

        return None

    def list_devices(self, role: Optional[str] = None) -> List[InventoryDevice]:
        """List all devices, optionally filtered by role.

        Args:
            role: Optional role filter (e.g., "core", "edge")

        Returns:
            List of devices
        """
        devices = list(self.devices.values())

        if role:
            devices = [d for d in devices if d.role == role]

        return devices

    def search_devices(self, query: str) -> List[InventoryDevice]:
        """Search devices by name, hostname, description, or location.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching devices
        """
        query_lower = query.lower()
        results = []

        for device in self.devices.values():
            if (
                query_lower in device.name.lower()
                or query_lower in device.hostname.lower()
                or (device.description and query_lower in device.description.lower())
                or (device.location and query_lower in device.location.lower())
            ):
                results.append(device)

        return results

    def get_device_names(self) -> List[str]:
        """Get list of all device names.

        Returns:
            List of device names
        """
        return list(self.devices.keys())

    def save_to_file(self, file_path: str):
        """Save inventory to file.

        Args:
            file_path: Path to save file
        """
        path = Path(file_path)

        data = {"devices": [device.to_dict() for device in self.devices.values()]}

        with open(path, "w") as f:
            if path.suffix in [".yaml", ".yml"]:
                yaml.dump(data, f, default_flow_style=False)
            elif path.suffix == ".json":
                json.dump(data, f, indent=2)
            else:
                raise NetworkAgentError(
                    f"Unsupported format: {path.suffix}. Use .yaml or .json"
                )

        logger.info(f"Saved inventory to {file_path}")

    def add_device(self, device: InventoryDevice):
        """Add a device to inventory.

        Args:
            device: Device to add
        """
        self.devices[device.name] = device
        logger.info(f"Added device '{device.name}' to inventory")

    def remove_device(self, name: str) -> bool:
        """Remove a device from inventory.

        Args:
            name: Device name

        Returns:
            True if removed, False if not found
        """
        if name in self.devices:
            del self.devices[name]
            logger.info(f"Removed device '{name}' from inventory")
            return True
        return False

    def __len__(self) -> int:
        """Return number of devices in inventory."""
        return len(self.devices)

    def __contains__(self, name: str) -> bool:
        """Check if device exists in inventory."""
        return self.get_device(name) is not None
