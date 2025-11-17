"""Core command execution module."""

from netmiko import ConnectHandler


class CommandExecutor:
    """Executes commands on network devices."""

    def execute_command(self, command: str, device_session: ConnectHandler) -> str:
        """Execute a command on the connected device and return output."""
        try:
            output = device_session.send_command(command, read_timeout=10)
            return output.strip()
        except Exception as e:
            return f"Error executing command: {e!s}"
