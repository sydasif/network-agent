"""Device connection and command execution."""

import logging
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from .settings import settings
from .models import ConnectionStatus
from datetime import datetime
from typing import Optional

logger = logging.getLogger("net_agent.network_device")


class DeviceConnection:
    """Manage network device connection and commands - simplified version."""

    def __init__(self):
        """Initialize device connection handler."""
        self.connection = None
        self.device_config = None
        self.connected_at: Optional[datetime] = None

    def connect(self, hostname: str, username: str, password: str):
        """Connect to a network device with single attempt, fail fast.

        Args:
            hostname: Device IP or hostname
            username: SSH username
            password: SSH password

        Raises:
            ConnectionError: If connection fails with diagnostics
        """
        self.device_config = {
            "device_type": "cisco_ios",
            "host": hostname,
            "username": username,
            "password": password,
            "timeout": settings.connection_timeout,
            "session_timeout": settings.read_timeout,
            "auth_timeout": settings.connection_timeout,
            "banner_timeout": settings.banner_timeout,
            "fast_cli": False,
            "global_delay_factor": settings.global_delay_factor,
        }

        try:
            self.connection = ConnectHandler(**self.device_config)
            self.connected_at = datetime.now()
            logger.info(f"Connected to {hostname}")
        except NetmikoAuthenticationException as e:
            raise ConnectionError(
                f"\n❌ SSH Authentication Failed for {hostname}\n"
                f"   Please verify:\n"
                f"   • Device IP: {hostname}\n"
                f"   • Username: {username}\n"
                f"   • Password is correct\n"
                f"   • Device allows SSH access\n"
                f"   • Device is running (ping {hostname} first)\n"
                f"\n   Try manually: ssh {username}@{hostname}\n"
            ) from e

        except NetmikoTimeoutException as e:
            raise ConnectionError(
                f"\n❌ Connection Timeout for {hostname}\n"
                f"   Please verify:\n"
                f"   • Device IP is correct: {hostname}\n"
                f"   • Device is reachable (ping {hostname})\n"
                f"   • SSH is enabled on device\n"
                f"   • Firewall allows SSH (port 22)\n"
                f"   • Device is powered on"
            ) from e

        except Exception as e:
            raise ConnectionError(
                f"\n❌ Connection Failed: {e!s}\n"
                f"   Device: {hostname}\n"
                f"   Check device accessibility and credentials"
            ) from e

    def disconnect(self):
        """Disconnect from the device."""
        if self.connection:
            try:
                self.connection.disconnect()
                logger.info("Disconnected from device")
            except Exception as e:
                logger.warning(f"Disconnect error (non-critical): {e!s}")
            finally:
                self.connection = None
                self.connected_at = None

    def execute_command(self, command: str) -> str:
        """Execute a command on the device - simplified version without retry.

        Args:
            command: Command to execute

        Returns:
            Command output or detailed error message

        Raises:
            ConnectionError: If connection is dead
        """
        # Check if we have a connection object
        if not self.connection:
            raise ConnectionError(
                "❌ Not connected to device\n"
                "   Please restart the application and connect again"
            )

        # Check if connection is alive - a basic check without the complexity of state management
        if not self.connection.is_alive():
            raise ConnectionError(
                "❌ Not connected to device\n"
                "   Please restart the application and connect again"
            )

        # Execute command with proper error handling - no retry logic
        try:
            return self.connection.send_command(
                command,
                read_timeout=settings.command_timeout,
                expect_string=r"#",
            )

        except NetmikoTimeoutException as e:
            # CRITICAL: Check if it's a pattern detection issue vs real timeout
            error_str = str(e).lower()
            if "pattern not detected" in error_str or "pattern" in error_str:
                raise ConnectionError(
                    f"❌ Command pattern matching failed\n"
                    f"   Command: {command}\n"
                    f"   This usually happens with piped commands (|)\n"
                    f"   Try: Use simpler commands or increase timeout\n"
                    f"   Error: {e!s}"
                ) from e
            raise ConnectionError(
                f"❌ Command execution timeout\n"
                f"   Command: {command}\n"
                f"   Device may not respond"
            ) from e

        except Exception as e:
            raise ConnectionError(
                f"❌ Command execution failed\n   Command: {command}\n   Error: {e!s}"
            ) from e

    def get_connection_status(self) -> ConnectionStatus:
        """Get current connection status information.

        Returns:
            ConnectionStatus object with connection details
        """
        connected = self.connection is not None
        device_hostname = self.device_config.get("host") if self.device_config else None
        return ConnectionStatus(
            connected=connected,
            device=device_hostname,
            established_at=self.connected_at,
        )
