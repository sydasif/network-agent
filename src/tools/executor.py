"""Tool for executing network commands.

This module provides a LangChain tool for executing read-only CLI commands on
network devices. It leverages the NetworkManager to establish connections and
execute commands safely, with proper error handling and output sanitization.
"""

from langchain_core.tools import tool
from src.core.models import CommandOutput
from src.tools.inventory import network_manager  # Reuse the same instance


@tool
def run_network_command(device_name: str, command: str) -> CommandOutput:
    """Executes a read-only CLI command on a specified network device.

    This tool allows execution of read-only ('show') commands on network devices
    to retrieve operational status or configuration information. It uses the
    NetworkManager to handle connections and includes error handling and output
    sanitization.

    Args:
        device_name (str): The name of the device to execute the command on.
        command (str): The CLI command to execute (should be a read-only command).

    Returns:
        CommandOutput: An object containing the command execution results,
        including the output, device name, command executed, and any error
        information if the command failed.
    """
    try:
        output = network_manager.execute_command(device_name, command)
        return CommandOutput(device_name=device_name, command=command, output=output)
    except Exception as e:
        return CommandOutput(
            device_name=device_name,
            command=command,
            output="",
            status="error",
            error_message=str(e),
        )
