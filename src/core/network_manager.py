"""Core module for managing network device connections and commands.

This module provides the NetworkManager class which handles device inventory management,
establishes connections to network devices, and executes commands using Netmiko (SSH/CLI).
It includes safety features like dangerous command detection and output sanitization.
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass
import yaml
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import functools


@dataclass
class Device:
    """Represents a network device with connection details.

    This data class stores all the necessary information to connect to and interact
    with a network device, including authentication credentials and protocol information.

    Attributes:
        name (str): Unique name identifier for the device.
        hostname (str): IP address or hostname of the device.
        username (str): Username for device authentication.
        password (str): Password for device authentication.
        device_type (str): Netmiko device type (e.g., 'cisco_ios', 'cisco_xr').
        description (str): Optional description of the device.
        role (str): Role of the device in the network (e.g., 'access', 'distribution').
    """

    name: str
    hostname: str
    username: str
    password: str
    device_type: str
    description: str = ""
    role: str = ""


class NetworkManager:
    """Manages inventory, connections, and command execution for network devices.

    The NetworkManager handles the lifecycle of network device connections, including
    loading device inventory from configuration files, establishing connections,
    executing commands, and managing session state. It supports multiple protocols
    and includes security measures to prevent dangerous operations.

    Attributes:
        inventory_file (str): Path to the inventory YAML file.
        devices (Dict[str, Device]): Dictionary mapping device names to Device objects.
        sessions (Dict[str, ConnectHandler]): Active Netmiko connections to devices.
    """

    def __init__(self, inventory_file: str = None):
        """Initializes the NetworkManager and loads device inventory.

        Args:
            inventory_file (str, optional): Path to inventory file. Uses default if None.
        """
        from src.core.config import settings
        self.inventory_file = inventory_file or settings.inventory_file
        self.devices: Dict[str, Device] = self._load_inventory()
        self.sessions: Dict[str, ConnectHandler] = {}

    def _load_inventory(self) -> Dict[str, Device]:
        """Loads device inventory from a YAML file.

        Returns:
            Dict[str, Device]: Dictionary mapping device names to Device objects.
        """
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
        """Retrieves a device by its name.

        Args:
            device_name (str): Name of the device to retrieve.

        Returns:
            Optional[Device]: Device object if found, None otherwise.
        """
        return self.devices.get(device_name)

    def execute_command(self, device_name: str, command: str) -> str:
        """Executes a command on a device using Netmiko.

        This method routes the command execution to the Netmiko protocol handler.

        Args:
            device_name (str): Name of the device to execute the command on.
            command (str): The command to execute on the device.

        Returns:
            str: The output of the executed command.

        Raises:
            ValueError: If the device is not found or command is dangerous.
        """
        device = self.get_device(device_name)
        if not device:
            raise ValueError(f"Device '{device_name}' not found in inventory.")

        # Currently only Netmiko is supported
        return self._execute_netmiko_command(device, command)

    def _execute_netmiko_command(self, device: Device, command: str) -> str:
        """Executes a command using Netmiko (CLI/SSH).

        Establishes a connection if needed, executes the command, and sanitizes the output.

        Args:
            device (Device): The device object to execute the command on.
            command (str): The command to execute.

        Returns:
            str: Sanitized output of the command.
        """
        if self._is_dangerous_command(command):
            raise ValueError(
                f"Execution blocked for potentially dangerous command: {command}"
            )

        if device.name not in self.sessions:
            try:
                self.sessions[device.name] = ConnectHandler(
                    device_type=device.device_type,
                    host=device.hostname,
                    username=device.username,
                    password=device.password,
                    timeout=10,
                )
            except NetmikoTimeoutException:
                raise ValueError(f"Timeout connecting to device {device.name}")
            except NetmikoAuthenticationException:
                raise ValueError(f"Authentication failed for device {device.name}")
            except Exception as e:
                raise ValueError(f"Failed to connect to device {device.name}: {e}")

        session = self.sessions[device.name]
        try:
            output = session.send_command(command, read_timeout=20)
            return self._sanitize_output(output)
        except NetmikoTimeoutException:
            raise ValueError(f"Timeout executing command '{command}' on device {device.name}")
        except Exception as e:
            raise ValueError(f"Error executing command '{command}' on device {device.name}: {e}")

    # Cache compiled regex patterns to avoid recompilation
    _DANGEROUS_PATTERNS_COMPILED = [
        re.compile(r"write\s+erase", re.IGNORECASE),
        re.compile(r"reload", re.IGNORECASE),
        re.compile(r"delete", re.IGNORECASE),
        re.compile(r"format", re.IGNORECASE),
        re.compile(r"configure\s+terminal", re.IGNORECASE),
        re.compile(r"no\s+shutdown", re.IGNORECASE),
        re.compile(r"clear", re.IGNORECASE),
        re.compile(r"tclsh", re.IGNORECASE),  # Prevent scripting execution
        re.compile(r"bash", re.IGNORECASE),   # Prevent shell access on some devices
        re.compile(r"enable\s+secret", re.IGNORECASE),
        re.compile(r"username.*secret", re.IGNORECASE),
        re.compile(r"service.*password", re.IGNORECASE),
        # Patterns with potential for command injection - be more specific with shell separators
        # Only block ; and & as dangerous, allow | as it's commonly used in network commands
        re.compile(r"^[;&]", re.IGNORECASE),  # Shell command separators at start (excluding pipe)
        re.compile(r"[;&][;&|]", re.IGNORECASE),  # Multiple separators starting with ; or &
        re.compile(r"[;&]\s*[;&|]", re.IGNORECASE),  # Multiple separators with space
    ]

    def _is_dangerous_command(self, command: str) -> bool:
        """Checks for potentially harmful commands.

        Prevents execution of commands that could damage the network infrastructure.

        Args:
            command (str): The command to check.

        Returns:
            bool: True if the command is dangerous, False otherwise.
        """
        command_lower = command.lower().strip()

        # Additional validation: check for potentially encoded dangerous commands
        # Convert common substitutions back to check for dangerous patterns
        deobfuscated_command = command_lower
        # Common character substitutions in commands (e.g., "w r i t e" for "write")
        deobfuscated_command = re.sub(r'\s+', '', deobfuscated_command)  # Remove internal spaces
        # Add more deobfuscation patterns as needed

        # Check both original and deobfuscated versions
        return any(
            pattern.search(command_lower) or pattern.search(deobfuscated_command)
            for pattern in self._DANGEROUS_PATTERNS_COMPILED
        )

    def _sanitize_output(self, output: str) -> str:
        """Removes sensitive information from CLI output.

        This method redacts passwords and secrets from command output for security.

        Args:
            output (str): The raw command output.

        Returns:
            str: Sanitized output with sensitive information redacted.
        """
        # Simplified for brevity; a production version would be more robust.
        result = re.sub(
            r"password\s+\S+", "password [REDACTED]", output, flags=re.IGNORECASE
        )
        result = re.sub(
            r"secret\s+\S+", "secret [REDACTED]", result, flags=re.IGNORECASE
        )
        return result

    def close_all_sessions(self):
        """Closes all active Netmiko sessions.

        This method ensures all connections are properly closed when the manager is shut down.
        """
        for session in self.sessions.values():
            if session.is_alive():
                session.disconnect()
        self.sessions.clear()
