"""LangChain tool for executing show/display/get commands on network devices."""

import logging
from typing import Optional
from langchain_core.tools import tool

from ..command_executor import CommandExecutor
from ..audit import AuditLogger


logger = logging.getLogger("net_agent.tools.execute_show")


@tool
def execute_show(command: str) -> str:
    """Run a validated show/display/get command on the active device.
    
    Args:
        command: The show command to execute (e.g., 'show version', 'show ip int brief')
        
    Returns:
        str: The command output or error message
    """
    # This function requires access to the command executor and session
    # which will be provided via closure or dependency injection
    raise NotImplementedError(
        "This tool requires access to the command executor and session."
        "It will be properly initialized when the agent is created."
    )


class ExecuteShowTool:
    """Class to properly initialize the execute_show tool with required dependencies."""
    
    def __init__(self, command_executor: CommandExecutor, session_manager=None):
        self.command_executor = command_executor
        self.session_manager = session_manager

    def create_tool(self):
        """Create and return the execute_show tool with proper dependencies."""
        
        @tool
        def execute_show_tool(command: str) -> str:
            """Run a validated show/display/get command on the active device.
            
            Args:
                command: The show command to execute (e.g., 'show version', 'show ip int brief')
                
            Returns:
                str: The command output or error message
            """
            if not self.session_manager or not self.session_manager.get_current_connection():
                return "❌ No active device connection. Please connect to a device first."

            try:
                result = self.command_executor.execute_command(command, self.session_manager.get_current_connection())
                return result
            except Exception as e:
                logger.error(f"Error executing command '{command}': {e}")
                return f"❌ Error executing command: {str(e)}"

        return execute_show_tool