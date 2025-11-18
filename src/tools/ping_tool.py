"""Tool for executing ping commands for network connectivity checks.

This module provides a LangChain tool for executing ping commands to test network
connectivity to specific IP addresses or hostnames. It leverages system ping
utility and returns structured results.
"""

import subprocess
import platform
from typing import Optional
from langchain_core.tools import tool
from src.core.models import CommandOutput


@tool
def ping_host(
    target: str, count: Optional[int] = 4, timeout: Optional[int] = 5
) -> CommandOutput:
    """Pings a specified IP address or hostname to test network connectivity.

    This tool executes a ping command to verify network connectivity to a specific
    destination. It works on both Windows and Unix-like systems (Linux/Mac).

    Args:
        target (str): The IP address or hostname to ping (e.g., "8.8.8.8" or "google.com")
        count (int, optional): Number of ping packets to send. Defaults to 4.
        timeout (int, optional): Timeout in seconds for each ping packet. Defaults to 5.

    Returns:
        CommandOutput: An object containing the ping command results,
        including the output, target, command executed, and any error
        information if the command failed.
    """
    try:
        # Determine the ping command based on the operating system
        system = platform.system().lower()
        if system == "windows":
            # On Windows, use -n for count and -w for timeout (in milliseconds)
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), target]
        else:
            # On Linux/Mac, use -c for count and -W for timeout (in seconds)
            cmd = ["ping", "-c", str(count), "-W", str(timeout), target]

        # Execute the ping command, with an overall timeout to prevent hanging
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout * count + 5,  # Add extra time to ensure command completes
        )

        # Determine the status based on return code
        status = "success" if result.returncode == 0 else "error"
        output = result.stdout

        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"

        return CommandOutput(
            device_name=target,  # For ping, we'll use target as device name
            command=f"ping {target} -c {count}",
            output=output,
            status=status,
            error_message=None
            if result.returncode == 0
            else f"Command failed with return code {result.returncode}",
        )
    except subprocess.TimeoutExpired:
        return CommandOutput(
            device_name=target,
            command=f"ping {target} -c {count}",
            output="",
            status="error",
            error_message="Ping command timed out",
        )
    except Exception as e:
        return CommandOutput(
            device_name=target,
            command=f"ping {target} -c {count}",
            output="",
            status="error",
            error_message=str(e),
        )
