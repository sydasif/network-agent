"""Core module for managing network device connections and commands."""
import re
from typing import Dict, Optional
from dataclasses import dataclass, field
import yaml
from netmiko import ConnectHandler

@dataclass
class Device:
    """Represents a network device with connection details."""
    name: str
    hostname: str
    username: str
    password: str
    device_type: str
    description: str = ""
    role: str = ""
    connection_protocol: str = "netmiko"

class NetworkManager:
    """Manages inventory, connections, and command execution for network devices."""
    def __init__(self, inventory_file: str = "inventory.yaml"):
        self.inventory_file = inventory_file
        self.devices: Dict[str, Device] = self._load_inventory()
        self.sessions: Dict[str, ConnectHandler] = {}

    def _load_inventory(self) -> Dict[str, Device]:
        """Loads device inventory from a YAML file."""
        try:
            with open(self.inventory_file, "r") as f:
                data = yaml.safe_load(f)
            return {
                dev_data["name"]: Device(**dev_data)
                for dev_data in data.get("devices", [])
            }
        except Exception as e:
            print(f"Error loading inventory: {e}")
            return {}

    def get_device(self, device_name: str) -> Optional[Device]:
        """Retrieves a device by its name."""
        return self.devices.get(device_name)

    def execute_command(self, device_name: str, command: str) -> str:
        """
        Executes a command on a device, dispatching to the correct protocol handler.
        """
        device = self.get_device(device_name)
        if not device:
            raise ValueError(f"Device '{device_name}' not found in inventory.")

        if device.connection_protocol == "netmiko":
            return self._execute_netmiko_command(device, command)
        elif device.connection_protocol == "gnmi":
            return self._execute_gnmi_get(device, command)
        else:
            raise NotImplementedError(f"Protocol '{device.connection_protocol}' is not supported.")

    def _execute_netmiko_command(self, device: Device, command: str) -> str:
        """Executes a command using Netmiko (CLI/SSH)."""
        if self._is_dangerous_command(command):
            raise ValueError(f"Execution blocked for potentially dangerous command: {command}")

        if device.name not in self.sessions:
            self.sessions[device.name] = ConnectHandler(
                device_type=device.device_type,
                host=device.hostname,
                username=device.username,
                password=device.password,
                timeout=10,
            )

        session = self.sessions[device.name]
        output = session.send_command(command, read_timeout=20)
        return self._sanitize_output(output)

    def _execute_gnmi_get(self, device: Device, xpath: str) -> str:
        """Placeholder for executing a gNMI GET request."""
        # In a real implementation, you would use a library like pygnmi here.
        # For now, this demonstrates the dispatcher pattern.
        raise NotImplementedError(
            f"gNMI not implemented. Attempted to query {device.name} with path: {xpath}"
        )

    def _is_dangerous_command(self, command: str) -> bool:
        """Checks for potentially harmful commands."""
        dangerous_patterns = [r"write\s+erase", r"reload", r"delete", r"format", r"configure\s+terminal"]
        command_lower = command.lower().strip()
        return any(re.search(pattern, command_lower) for pattern in dangerous_patterns)

    def _sanitize_output(self, output: str) -> str:
        """Removes sensitive information from CLI output."""
        # Simplified for brevity; a production version would be more robust.
        output = re.sub(r"password\s+\S+", "password [REDACTED]", output, flags=re.IGNORECASE)
        output = re.sub(r"secret\s+\S+", "secret [REDACTED]", output, flags=re.IGNORECASE)
        return output

    def close_all_sessions(self):
        """Closes all active Netmiko sessions."""
        for session in self.sessions.values():
            if session.is_alive():
                session.disconnect()
        self.sessions.clear()
