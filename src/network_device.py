"""Device connection and command execution."""

import time
import random
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from .settings import settings


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
        self.max_retries = 3  # Maximum connection retries for transient issues

    def connect(self, hostname: str, username: str, password: str):
        """Connect to a network device with proper error handling and retry logic.

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
            "timeout": settings.connection_timeout,
            "session_timeout": settings.read_timeout,
            "auth_timeout": settings.connection_timeout,
            "banner_timeout": settings.banner_timeout,
            "fast_cli": False,
            "global_delay_factor": settings.global_delay_factor,
        }

        # Try to connect with retry logic for transient network issues
        for attempt in range(1, self.max_retries + 1):
            try:
                self.connection = ConnectHandler(**self.device_config)
                self.state = ConnectionState.CONNECTED
                self.last_error = None
                print(f"✓ Connected to {hostname}")
                return  # Successful connection, exit the retry loop

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
                # For timeout issues, we might want to try again after a delay
                if attempt < self.max_retries:
                    print(f"⚠️  Connection attempt {attempt} failed (timeout), retrying in {attempt} seconds...")
                    time.sleep(attempt)  # Exponential backoff (simple version)
                    continue
                else:
                    self.state = ConnectionState.FAILED
                    self.last_error = "Connection timeout after retries"
                    raise ConnectionError(
                        f"\n❌ Connection Timeout for {hostname} (after {self.max_retries} attempts)\n"
                        f"   Please verify:\n"
                        f"   • Device IP is correct: {hostname}\n"
                        f"   • Device is reachable (ping {hostname})\n"
                        f"   • SSH is enabled on device\n"
                        f"   • Firewall allows SSH (port 22)\n"
                        f"   • Device is powered on"
                    ) from e

            except Exception as e:
                # For other exceptions, check if it's worth retrying
                error_str = str(e).lower()
                if "timeout" in error_str or "refused" in error_str or "reset" in error_str:
                    if attempt < self.max_retries:
                        print(f"⚠️  Connection attempt {attempt} failed, retrying in {attempt} seconds...")
                        time.sleep(attempt)  # Exponential backoff (simple version)
                        continue

                self.state = ConnectionState.FAILED
                self.last_error = str(e)
                raise ConnectionError(
                    f"\n❌ Connection Failed: {e!s}\n"
                    f"   Device: {hostname}\n"
                    f"   Attempt: {attempt}/{self.max_retries}\n"
                    f"   Check device accessibility and credentials"
                ) from e

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
            ConnectionError: If connection is dead
        """
        # Check if we have a connection object
        if not self.connection or not self.connection.is_alive():
            self.state = ConnectionState.FAILED
            self.last_error = "Connection is not alive"
            raise ConnectionError(
                "❌ Not connected to device\n"
                "   Please restart the application and connect again"
            )

        # Execute command with proper error handling
        try:
            # CRITICAL: Add expect_string parameter to help Netmiko find the prompt
            # Increase read_timeout for piped commands (they can be slow)
            output = self.connection.send_command(
                command,
                read_timeout=settings.command_timeout,  # Use config value
                expect_string=r"#",  # Explicitly tell Netmiko to look for #
            )
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
                # For timeout issues during command execution, try once more before failing
                if "timeout" in error_str:
                    print("⚠️  Command timeout, trying again...")
                    try:
                        output = self.connection.send_command(
                            command,
                            read_timeout=settings.command_timeout * 2,  # Double timeout for retry
                            expect_string=r"#",
                        )
                        return output
                    except Exception:
                        # If retry also fails, raise the original error
                        pass
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
        is_alive = self.connection.is_alive() if self.connection else False
        # Only update state to FAILED if we previously had a connection but it's no longer alive
        if not is_alive and self.connection and self.state == ConnectionState.CONNECTED:
            self.state = ConnectionState.FAILED
        return {
            "state": self.state,
            "connected": self.state == ConnectionState.CONNECTED and is_alive,
            "is_alive": is_alive,
            "device": self.device_config.get("host") if self.device_config else None,
            "last_error": self.last_error,
        }
