"""Device connection and command execution."""

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
import threading


class ConnectionState:
    """Connection state tracking."""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    FAILED = "failed"


class DeviceConnection:
    """Manage network device connection and commands with state tracking."""

    def __init__(self, conn_config=None):
        """Initialize device connection handler."""
        self.connection = None
        self.state = ConnectionState.DISCONNECTED
        self.device_config = None
        self.last_error = None
        self.connection_attempts = 0

        if conn_config is not None:
            self.conn_config = conn_config
            self.max_reconnect_attempts = conn_config.max_reconnect_attempts
        else:
            # Default values for backward compatibility
            from .config import ConnectionConfig
            self.conn_config = ConnectionConfig()
            self.max_reconnect_attempts = self.conn_config.max_reconnect_attempts

        # CRITICAL: Add thread lock to prevent concurrent reconnection attempts
        self._connection_lock = threading.Lock()

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
            "timeout": self.conn_config.connection_timeout,
            "session_timeout": self.conn_config.read_timeout,
            "auth_timeout": self.conn_config.connection_timeout,
            "banner_timeout": self.conn_config.banner_timeout,
            # CRITICAL: Add fast_cli to prevent pattern matching issues with piped commands
            "fast_cli": False,  # Disable fast mode for better reliability
            "global_delay_factor": self.conn_config.global_delay_factor,  # Increase delay for slow devices
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
                f"\n   Try manually: ssh {username}@{hostname}\n"
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
            # CRITICAL: Use a very simple command with generous timeout
            # Don't use piped commands for liveness check
            self.connection.send_command("show clock", read_timeout=10, expect_string=r"#")
            return True
        except Exception:
            return False

    def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect to the device.

        Returns:
            True if reconnection successful, False otherwise
        """
        # CRITICAL: Use thread lock to prevent multiple simultaneous reconnection attempts
        with self._connection_lock:
            # Check if another thread already reconnected
            if self._is_connection_alive():
                return True

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
                self.connection_attempts = 0  # Reset on success
                print(f"✓ Reconnected successfully")
                return True

            except Exception as e:
                self.state = ConnectionState.FAILED
                self.last_error = f"Reconnect failed: {e!s}"
                print(f"❌ Reconnect attempt {self.connection_attempts} failed: {e!s}")
                return False

    def disconnect(self):
        """Disconnect from the device."""
        with self._connection_lock:
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

        # Check if connection is still alive (but don't reconnect yet)
        if not self._is_connection_alive():
            # Attempt to reconnect (thread-safe)
            if not self._attempt_reconnect():
                raise ConnectionError(
                    f"❌ Connection lost and reconnection failed\n"
                    f"   Attempts: {self.connection_attempts}/{self.max_reconnect_attempts}\n"
                    f"   Last error: {self.last_error}\n"
                    f"   Please restart the application and reconnect"
                )

        # Execute command with proper error handling
        try:
            # CRITICAL: Add expect_string parameter to help Netmiko find the prompt
            # Increase read_timeout for piped commands (they can be slow)
            output = self.connection.send_command(
                command,
                read_timeout=self.conn_config.command_timeout,  # Use config value
                expect_string=r"#",  # Explicitly tell Netmiko to look for #
            )
            self.connection_attempts = 0  # Reset counter on success
            return output

        except NetmikoTimeoutException as e:
            self.state = ConnectionState.FAILED
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
            else:
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
