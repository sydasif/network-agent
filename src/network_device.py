"""Device connection and command execution."""

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException


class ConnectionState:
    """Connection state tracking."""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    FAILED = "failed"


class DeviceConnection:
    """Manage network device connection and commands with state tracking."""

    def __init__(self):
        """Initialize device connection handler."""
        self.connection = None
        self.state = ConnectionState.DISCONNECTED
        self.device_config = None
        self.last_error = None
        self.connection_attempts = 0
        self.max_reconnect_attempts = 3

    def connect(self, hostname: str, username: str, password: str):
        """Connect to a network device with proper error handling.

        Args:
            hostname: Device IP or hostname
            username: SSH username
            password: SSH password

        Raises:
            ConnectionError: If connection fails after proper diagnostics
        """
        self.device_config = {
            "device_type": "cisco_ios",
            "host": hostname,
            "username": username,
            "password": password,
            "timeout": 30,
            "session_timeout": 60,  # Add session timeout
            "auth_timeout": 30,     # Add auth timeout
            "banner_timeout": 15,   # Add banner timeout
        }

        try:
            self.connection = ConnectHandler(**self.device_config)
            self.state = ConnectionState.CONNECTED
            self.last_error = None
            self.connection_attempts = 0
            print(f"✓ Connected to {hostname}")

        except NetmikoAuthenticationException as e:
            self.state = ConnectionState.FAILED
            self.last_error = "Authentication failed"
            raise ConnectionError(
                f"\n❌ SSH Authentication Failed for {hostname}\n"
                f"   Please verify:\n"
                f"   • Device IP: {hostname}\n"
                f"   • Username: {username}\n"
                f"   • Password is correct\n"
                f"   • Device allows SSH access\n"
                f"   • Device is running (ping {hostname} first)\n"
                f"\n   Try manually: ssh {username}@{hostname}"
            ) from e

        except NetmikoTimeoutException as e:
            self.state = ConnectionState.FAILED
            self.last_error = "Connection timeout"
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
            self.state = ConnectionState.FAILED
            self.last_error = str(e)
            raise ConnectionError(
                f"\n❌ Connection Failed: {e!s}\n"
                f"   Device: {hostname}\n"
                f"   Check device accessibility and credentials"
            ) from e

    def _is_connection_alive(self) -> bool:
        """Check if connection is still alive.

        Returns:
            True if connection is alive, False otherwise
        """
        if not self.connection:
            return False

        try:
            # Send a simple command to check if connection is alive
            # Use a fast command with short timeout
            self.connection.send_command("show clock", read_timeout=5)
            return True
        except Exception:
            return False

    def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect to the device.

        Returns:
            True if reconnection successful, False otherwise
        """
        if not self.device_config:
            return False

        if self.connection_attempts >= self.max_reconnect_attempts:
            return False

        self.connection_attempts += 1

        try:
            print(f"⚠️  Connection lost. Attempting reconnect ({self.connection_attempts}/{self.max_reconnect_attempts})...")

            # Close dead connection
            if self.connection:
                try:
                    self.connection.disconnect()
                except Exception:
                    pass

            # Attempt new connection
            self.connection = ConnectHandler(**self.device_config)
            self.state = ConnectionState.CONNECTED
            self.last_error = None
            print(f"✓ Reconnected successfully")
            return True

        except Exception as e:
            self.state = ConnectionState.FAILED
            self.last_error = f"Reconnect failed: {e!s}"
            print(f"❌ Reconnect attempt {self.connection_attempts} failed: {e!s}")
            return False

    def disconnect(self):
        """Disconnect from the device."""
        if self.connection:
            try:
                self.connection.disconnect()
                print("✓ Disconnected")
            except Exception as e:
                print(f"⚠️  Disconnect error (non-critical): {e!s}")
            finally:
                self.connection = None
                self.state = ConnectionState.DISCONNECTED

    def execute_command(self, command: str) -> str:
        """Execute a command on the device with connection state management.

        Args:
            command: Command to execute

        Returns:
            Command output or detailed error message

        Raises:
            ConnectionError: If connection is dead and cannot reconnect
        """
        # Check if we have a connection object
        if not self.connection:
            raise ConnectionError(
                "❌ Not connected to device\n"
                "   Please restart the application and connect again"
            )

        # Check if connection is still alive
        if not self._is_connection_alive():
            # Attempt to reconnect
            if not self._attempt_reconnect():
                raise ConnectionError(
                    f"❌ Connection lost and reconnection failed\n"
                    f"   Attempts: {self.connection_attempts}/{self.max_reconnect_attempts}\n"
                    f"   Last error: {self.last_error}\n"
                    f"   Please restart the application and reconnect"
                )

        # Execute command with proper error handling
        try:
            output = self.connection.send_command(command, read_timeout=30)
            self.connection_attempts = 0  # Reset counter on success
            return output

        except NetmikoTimeoutException as e:
            self.state = ConnectionState.FAILED
            raise ConnectionError(
                f"❌ Command execution timeout\n"
                f"   Command: {command}\n"
                f"   Device may be unresponsive or command takes too long"
            ) from e

        except Exception as e:
            self.state = ConnectionState.FAILED
            self.last_error = str(e)
            raise ConnectionError(
                f"❌ Command execution failed\n"
                f"   Command: {command}\n"
                f"   Error: {e!s}"
            ) from e

    def get_connection_status(self) -> dict:
        """Get current connection status information.

        Returns:
            Dictionary with connection status details
        """
        return {
            "state": self.state,
            "connected": self.state == ConnectionState.CONNECTED,
            "is_alive": self._is_connection_alive() if self.connection else False,
            "device": self.device_config.get("host") if self.device_config else None,
            "last_error": self.last_error,
            "reconnect_attempts": self.connection_attempts,
        }
