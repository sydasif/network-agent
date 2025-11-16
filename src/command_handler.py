"""Command handler for special commands in network automation."""

import logging
from typing import Tuple

from .devices import Registry
from .utils import print_line_separator


logger = logging.getLogger("net_agent.command_handler")


class CommandHandler:
    """Handle special commands like inventory, connected, switch, etc."""
    
    def __init__(self, device_registry: Registry):
        """Initialize command handler."""
        self.device_registry = device_registry
    
    def handle_special_command(self, command: str) -> Tuple[bool, str]:
        """Handle special commands.
        
        Args:
            command: User input command
            
        Returns:
            Tuple of (is_special_command, response)
        """
        cmd_lower = command.strip().lower()

        if cmd_lower == "inventory":
            return True, self._show_inventory()
        
        if cmd_lower == "connected":
            return True, self._show_connected_devices()
        
        if cmd_lower.startswith("switch "):
            device_name = cmd_lower[7:].strip().upper()  # Get device name after "switch "
            return True, self._switch_device(device_name)
        
        if cmd_lower.startswith("disconnect "):
            device_name = cmd_lower[11:].strip().upper()  # Get device name after "disconnect "
            return True, self._disconnect_device(device_name)
        
        if cmd_lower in ["help", "h"]:
            return True, self._show_help()
        
        return False, ""
    
    def _show_inventory(self) -> str:
        """Display the device inventory."""
        output = []
        output.append("\n📦 Device Inventory:")
        output.append("")

        # Group devices by role
        roles = {"core": [], "distribution": [], "access": [], "edge": [], "other": []}

        for device in self.device_registry.list_devices():
            role = device.role.lower() if device.role else "other"
            if role in roles:
                roles[role].append(device)
            else:
                roles["other"].append(device)

        # Display roles in order
        role_order = ["core", "distribution", "access", "edge", "other"]
        for role in role_order:
            if roles[role]:
                output.append(f"  {role.upper()}:")
                for device in sorted(roles[role], key=lambda d: d.name):
                    status = "✓" if self.device_registry.is_connected(device.name) else "○"
                    output.append(
                        f"    {status} {device.name:<15} {device.hostname:<15} {device.description or ''}"
                    )
                output.append("")

        if not any(roles.values()):
            output.append("  No devices in inventory.")
        
        return "\n".join(output)
    
    def _show_connected_devices(self) -> str:
        """Display connected devices."""
        output = []
        output.append("\n🔌 Connected Devices:")
        output.append("")

        connected_devices = self.device_registry.get_connected()
        current_device = self.device_registry.get_current_name()

        if connected_devices:
            for device_name, connection in connected_devices.items():
                status = "✓"
                marker = "  →" if device_name == current_device else "   "
                output.append(
                    f"{marker} {status} {device_name:<15} {connection.device_config['host']}"
                )
        else:
            output.append("  No devices currently connected.")
        
        return "\n".join(output)
    
    def _switch_device(self, device_name: str) -> str:
        """Switch to a specific device."""
        if device_name not in self.device_registry:
            return f"❌ Device '{device_name}' not found in inventory\n💡 Available devices: {', '.join(self.device_registry.inventory_manager.get_device_names())}"
        elif not self.device_registry.is_connected(device_name):
            return f"❌ Device '{device_name}' is not connected"
        else:
            try:
                self.device_registry.switch(device_name)
                return f"✓ Switched to device: {device_name}"
            except ValueError as e:
                return f"❌ Could not switch to device '{device_name}': {e}"
    
    def _disconnect_device(self, device_name: str) -> str:
        """Disconnect from a specific device."""
        if not self.device_registry.is_connected(device_name):
            return f"❌ Device '{device_name}' is not connected"
        else:
            success = self.device_registry.disconnect(device_name)
            if success:
                return f"✓ Disconnected from device: {device_name}"
            else:
                return f"❌ Failed to disconnect from device: {device_name}"
    
    def _show_help(self) -> str:
        """Show help information."""
        help_text = """
💡 Help - Available Commands:

  • Ask naturally: 'show vlans on SW1' or 'check RTR1 uptime'
  • inventory      - Show all devices in inventory
  • connected      - Show currently connected devices
  • switch NAME    - Manually switch to a device (e.g., 'switch RTR1')
  • disconnect NAME- Disconnect from a device (e.g., 'disconnect SW1')
  • help           - Show this help
  • quit           - Exit application

  Natural language patterns:
  • 'show version on RTR1'    - Connect to RTR1 and execute command
  • 'get interfaces from SW1' - Connect to SW1 and execute command
  • 'check status at SW2'     - Connect to SW2 and execute command
  • 'what's the uptime for RTR1' - Connect to RTR1 and execute command
  • 'show configuration of SW1' - Connect to SW1 and execute command
"""
        return help_text