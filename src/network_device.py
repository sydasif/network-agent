"""Device connection and command execution."""

from netmiko import ConnectHandler


class DeviceConnection:
    """Manage network device connection and commands."""

    def __init__(self):
        """Initialize device connection handler."""
        self.connection = None

    def connect(self, hostname: str, username: str, password: str):
        """Connect to a network device."""
        device_config = {
            'device_type': 'cisco_ios',
            'host': hostname,
            'username': username,
            'password': password,
            'timeout': 30,
        }
        try:
            self.connection = ConnectHandler(**device_config)
            print(f"✓ Connected to {hostname}")
        except Exception as e:
            error_msg = str(e).lower()
            if 'authentication' in error_msg or 'auth' in error_msg:
                raise ConnectionError(
                    f"\n❌ SSH Authentication Failed for {hostname}\n"
                    f"   Please verify:\n"
                    f"   • Device IP: {hostname}\n"
                    f"   • Username: {username}\n"
                    f"   • Password is correct\n"
                    f"   • Device allows SSH access\n"
                    f"   • Device is running (ping {hostname} first)\n"
                    f"\n   Try manually: ssh {username}@{hostname}"
                )
            if 'timeout' in error_msg or 'refused' in error_msg:
                raise ConnectionError(
                    f"\n❌ Connection Timeout/Refused for {hostname}\n"
                    f"   Please verify:\n"
                    f"   • Device IP is correct: {hostname}\n"
                    f"   • Device is reachable (ping {hostname})\n"
                    f"   • SSH is enabled on device\n"
                    f"   • Firewall allows SSH (port 22)\n"
                    f"   • Device is powered on"
                )
            raise ConnectionError(
                f"\n❌ Connection Failed: {str(e)}\n"
                f"   Device: {hostname}\n"
                f"   Check device accessibility and credentials"
            )

    def disconnect(self):
        """Disconnect from the device."""
        if self.connection:
            self.connection.disconnect()
            print("✓ Disconnected")

    def execute_command(self, command: str) -> str:
        """Execute a command on the device."""
        if not self.connection:
            return "Error: Not connected to device"

        try:
            output = self.connection.send_command(command)
            return output
        except Exception as e:
            return f"Error: {str(e)}"
