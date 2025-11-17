from langchain_core.tools import tool

from src.core.network_manager import NetworkManager


# Initialize network manager
network_manager = NetworkManager("inventory.yaml")


@tool
def run_network_command(device_name: str, command: str) -> str:
    """
    Execute network CLI commands on devices.

    Use this tool when the user wants to:
    - Run show commands (show vlan, show interfaces, show version, etc.)
    - Get device configuration or status
    - Execute any CLI command on a network device

    Args:
        device_name: Name of the device to execute command on
        command: The CLI command to execute

    Returns: Sanitized CLI output from the device
    """
    try:
        return network_manager.execute_command(device_name, command)
    except ValueError as e:
        return f"Command error: {e}"
    except Exception as e:
        return f"Error executing command: {e}"
