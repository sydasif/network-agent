"""Tool for executing network commands."""
from langchain_core.tools import tool
from src.core.models import CommandOutput
from src.tools.inventory import network_manager # Reuse the same instance

@tool
def run_network_command(device_name: str, command: str) -> CommandOutput:
    """
    Executes a read-only CLI command on a specified network device.
    Use this for 'show' commands to get operational status or configuration.
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