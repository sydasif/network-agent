"""Core device manager module."""

from typing import Dict

from netmiko import ConnectHandler

from .inventory import Device


class DeviceManager:
    """Manages device connections and sessions."""

    def __init__(self):
        self.current_session = None
        self.session_cache: Dict[str, ConnectHandler] = {}

    def get_device_session(self, device: Device) -> ConnectHandler:
        """Get or create a session for the specified device."""
        if device.hostname in self.session_cache:
            return self.session_cache[device.hostname]

        # Create new session
        session = ConnectHandler(
            device_type=device.device_type,
            host=device.hostname,
            username=device.username,
            password=device.password,
            timeout=10,
        )

        self.session_cache[device.hostname] = session
        self.current_session = session
        return session

    def switch_device_session(self, device: Device) -> ConnectHandler:
        """Switch to a session for the specified device."""
        return self.get_device_session(device)

    def close_session(self, device_hostname: str):
        """Close the session for a specific device."""
        if device_hostname in self.session_cache:
            session = self.session_cache[device_hostname]
            try:
                session.disconnect()
            except:
                pass
            del self.session_cache[device_hostname]

    def disconnect_all(self):
        """Disconnect all active sessions."""
        for session in self.session_cache.values():
            try:
                session.disconnect()
            except:
                pass
        self.session_cache.clear()
