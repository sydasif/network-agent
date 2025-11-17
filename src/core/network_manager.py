"""Simplified network manager module."""
import re
from typing import Dict, Optional
from dataclasses import dataclass

import yaml
from netmiko import ConnectHandler


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


class NetworkManager:
    """Simplified network manager combining inventory, connection, and command execution."""

    def __init__(self, inventory_file: str = "inventory.yaml"):
        self.inventory_file = inventory_file
        self.devices: Dict[str, Device] = {}
        self.sessions: Dict[str, ConnectHandler] = {}

        # Load inventory
        self._load_inventory()

    def _load_inventory(self):
        """Load inventory from YAML file."""
        try:
            with open(self.inventory_file, "r") as f:
                data = yaml.safe_load(f)

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
                self.devices[device.name] = device

        except Exception as e:
            print(f"Error loading inventory: {e}")

    def get_device(self, device_name: str) -> Optional[Device]:
        """Get device by name."""
        return self.devices.get(device_name)

    def get_session(self, device_name: str) -> ConnectHandler:
        """Get or create a session for the specified device."""
        if device_name in self.sessions:
            return self.sessions[device_name]

        device = self.get_device(device_name)
        if not device:
            raise ValueError(f"Device '{device_name}' not found in inventory.")

        # Create new session
        session = ConnectHandler(
            device_type=device.device_type,
            host=device.hostname,
            username=device.username,
            password=device.password,
            timeout=10,
        )

        self.sessions[device_name] = session
        return session

    def execute_command(self, device_name: str, command: str) -> str:
        """Execute a command on the specified device."""
        # Basic security check - only allow safe commands
        if self._is_dangerous_command(command):
            raise ValueError(f"Potentially dangerous command detected: {command}")

        session = self.get_session(device_name)
        output = session.send_command(command, read_timeout=10)

        # Sanitize output
        return self._sanitize_output(output)

    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command is potentially dangerous."""
        dangerous_patterns = [
            r"write\s+erase",
            r"delete\s+",
            r"format\s+",
            r"no\s+shutdown",
            r"configure\s+terminal",
            r"wr\s+erase",
            r"del\s+",
            r"format\s",
            r"reload",
            r"no shutdown",
            r"ip route 0.0.0.0 0.0.0.0 null",
            r"username\s+\w+\s+privilege\s+15",
            r"enable secret",
            r"secret\s+0",
            r"no ip domain-lookup",
            r"default interface",
            r"clear counters",
        ]

        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return True
        return False

    def _sanitize_output(self, output: str) -> str:
        """Sanitize sensitive information from CLI output."""
        sensitive_patterns = [
            r"password\s+\S+",  # password followed by value
            r"secret\s+\d+\s+\S+",  # secret with level and value
            r"enable\s+secret\s+\S+",  # enable secret
            r"username\s+\S+\s+password\s+\S+",  # username with password
            r"key\s+\d+\s+\S+",  # key with value
            r"community\s+\S+\s+(RO|RW)",  # SNMP community strings
            r"(md5|sha)\s+\S+",  # Hash values that might be secrets
        ]

        cleaned_output = output
        for pattern in sensitive_patterns:
            # Replace sensitive data with [REDACTED]
            cleaned_output = re.sub(
                pattern,
                lambda m: m.group(0).split()[0] + " [REDACTED]",
                cleaned_output,
                flags=re.IGNORECASE,
            )

        return cleaned_output

    def close_session(self, device_name: str):
        """Close session for specific device."""
        if device_name in self.sessions:
            session = self.sessions[device_name]
            try:
                session.disconnect()
            except Exception:
                pass
            del self.sessions[device_name]

    def close_all_sessions(self):
        """Close all active sessions."""
        for session in self.sessions.values():
            try:
                session.disconnect()
            except Exception:
                pass
        self.sessions.clear()

