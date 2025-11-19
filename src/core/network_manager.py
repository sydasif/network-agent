"""Simplified module for managing network device connections and commands using Nornir.

This module provides the NetworkManager class which handles network device connections
using Nornir and executes commands using the nornir-netmiko plugin.
"""

from typing import Dict, List
from functools import lru_cache

from nornir import InitNornir
from nornir_netmiko import netmiko_send_command

from src.core.config import settings


class NetworkManager:
    """Manages network device connections and command execution using Nornir.

    The NetworkManager handles network device connections through Nornir, which
    provides built-in inventory management, connection handling, and parallel execution.

    Attributes:
        nornir: The Nornir instance for managing network devices.
        _device_names_cache: Cache for device names to avoid repeated inventory access.
    """

    def __init__(self, config_file: str = "inventory/config.yaml"):
        """Initializes the NetworkManager with Nornir.

        Args:
            config_file (str): Path to the Nornir configuration file.
        """
        try:
            self.nornir = InitNornir(config_file=config_file)
        except Exception as e:
            print(f"Error initializing Nornir: {e}")
            self.nornir = InitNornir(
                inventory={
                    "plugin": "SimpleInventory",
                    "options": {
                        "host_file": f"{settings.nornir_inventory_dir}/hosts.yaml",
                        "group_file": f"{settings.nornir_inventory_dir}/groups.yaml",
                    },
                }
            )
        # Initialize cache for device names
        self._device_names_cache = None

    def get_device_names(self) -> List[str]:
        """Returns a list of all device names in the inventory.

        Returns:
            List[str]: List of device names in the inventory.
        """
        # Use cached device names if available
        if self._device_names_cache is not None:
            return self._device_names_cache

        # Cache the device names for future use
        self._device_names_cache = list(self.nornir.inventory.hosts.keys())
        return self._device_names_cache

    def execute_command(self, device_name: str, command: str) -> str:
        """Executes a command on a specific device using Nornir.

        Args:
            device_name (str): Name of the device to execute the command on.
            command (str): The command to execute on the device.

        Returns:
            str: The output of the executed command.

        Raises:
            ValueError: If the device is not found in inventory.
            Exception: If command execution fails.
        """
        # Filter the Nornir inventory to target the specific device
        filtered_nornir = self.nornir.filter(name=device_name)

        # Check if the device exists in the inventory
        if len(filtered_nornir.inventory.hosts) == 0:
            raise ValueError(f"Device '{device_name}' not found in inventory.")

        # Execute the command using the netmiko plugin
        result = filtered_nornir.run(task=netmiko_send_command, command_string=command)

        # Get the result for the specific host
        host_result = result[device_name]

        # Check if the command execution failed
        if host_result.failed:
            raise Exception(f"Command execution failed: {host_result.result}")

        # Return the command output
        return host_result.result

    def execute_command_on_multiple_devices(
        self, device_names: List[str], command: str
    ) -> Dict[str, str]:
        """Executes a command on multiple devices.

        Args:
            device_names (List[str]): List of device names to execute the command on.
            command (str): The command to execute on the devices.

        Returns:
            Dict[str, str]: Dictionary mapping device names to command outputs.
        """
        # Filter the Nornir inventory to target the specific devices
        filtered_nornir = self.nornir.filter(name=device_names)

        # Execute the command on all specified devices simultaneously
        results = filtered_nornir.run(task=netmiko_send_command, command_string=command)

        # Process results and collect outputs for each device
        outputs = {}
        for device_name in device_names:
            if device_name in results:
                host_result = results[device_name]
                if not host_result.failed:
                    # Store successful command output
                    outputs[device_name] = host_result.result
                else:
                    # Store error message for failed commands
                    outputs[device_name] = f"Error: {host_result.result}"

        # Return mapping of device names to their command outputs
        return outputs

    def close_all_sessions(self):
        """Closes all active Nornir sessions."""
        self.nornir.close_connections()
        # Clear the device names cache when closing sessions
        self._device_names_cache = None
