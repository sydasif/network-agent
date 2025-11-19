"""Simplified module for managing network device connections and commands using Nornir.

This module provides the NetworkManager class which handles network device connections
using Nornir and executes commands using the nornir-netmiko plugin.
"""

from typing import Dict, List, Optional
from nornir import InitNornir
from nornir.core.filter import F
from nornir_netmiko import netmiko_send_command
from src.core.config import settings


class NetworkManager:
    """Manages network device connections and command execution using Nornir.

    The NetworkManager handles network device connections through Nornir, which
    provides built-in inventory management, connection handling, and parallel execution.

    Attributes:
        nornir: The Nornir instance for managing network devices.
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
            # Create a minimal Nornir instance with basic settings
            self.nornir = InitNornir(
                inventory={
                    "plugin": "SimpleInventory",
                    "options": {
                        "host_file": f"{settings.nornir_inventory_dir}/hosts.yaml",
                        "group_file": f"{settings.nornir_inventory_dir}/groups.yaml",
                    },
                }
            )

    def get_device_names(self) -> List[str]:
        """Returns a list of all device names in the inventory.

        Returns:
            List[str]: List of device names in the inventory.
        """
        return list(self.nornir.inventory.hosts.keys())

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
        # Filter Nornir inventory to target specific device
        filtered_nornir = self.nornir.filter(name=device_name)

        if len(filtered_nornir.inventory.hosts) == 0:
            raise ValueError(f"Device '{device_name}' not found in inventory.")

        # Execute command using Nornir's netmiko plugin
        result = filtered_nornir.run(
            task=netmiko_send_command,
            command_string=command
        )

        # Get the result for the specific host
        host_result = result[device_name]

        if host_result.failed:
            raise Exception(f"Command execution failed: {host_result.result}")

        return host_result.result

    def execute_command_on_multiple_devices(self, device_names: List[str], command: str) -> Dict[str, str]:
        """Executes a command on multiple devices.

        Args:
            device_names (List[str]): List of device names to execute the command on.
            command (str): The command to execute on the devices.

        Returns:
            Dict[str, str]: Dictionary mapping device names to command outputs.
        """
        # Filter Nornir inventory to target specific devices
        filtered_nornir = self.nornir.filter(name=device_names)

        # Execute command using Nornir's netmiko plugin
        results = filtered_nornir.run(
            task=netmiko_send_command,
            command_string=command
        )

        outputs = {}
        for device_name in device_names:
            if device_name in results:
                host_result = results[device_name]
                if not host_result.failed:
                    outputs[device_name] = host_result.result
                else:
                    outputs[device_name] = f"Error: {host_result.result}"

        return outputs

    def close_all_sessions(self):
        """Closes all active Nornir sessions.

        This method ensures all connections are properly closed when the manager is shut down.
        """
        # Nornir typically manages connections automatically,
        # but we can disconnect all connections
        self.nornir.close_connections()
