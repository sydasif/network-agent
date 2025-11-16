"""Device routing and management for network automation."""

import logging
import re
from typing import Optional, Tuple

from .inventory import InventoryManager


logger = logging.getLogger("net_agent.device_router")


class DeviceRouter:
    """Handle device selection and routing based on natural language queries."""

    def __init__(self, device_manager, inventory_manager: InventoryManager):
        """Initialize device router."""
        self.device_manager = device_manager
        self.inventory_manager = inventory_manager

    def extract_device_reference(self, question: str) -> Tuple[Optional[str], str]:
        """Extract device name from natural language question.

        Examples:
        - "show me vlans on SW1" -> ("SW1", "show me vlans")
        - "what's the uptime on RTR1" -> ("RTR1", "what's the uptime")
        - "get ip route from EDGE-RTR-1" -> ("EDGE-RTR-1", "get ip route")
        - "show version" -> (None, "show version")

        Returns:
            Tuple of (device_name, cleaned_question)
        """
        # Pattern to match device references
        patterns = [
            r"\bon\s+([A-Z0-9_-]+)",  # "on SW1", "on RTR1"
            r"\bfrom\s+([A-Z0-9_-]+)",  # "from SW1", "from RTR1"
            r"\bat\s+([A-Z0-9_-]+)",  # "at SW1", "at RTR1"
            r"\bfor\s+([A-Z0-9_-]+)",  # "for SW1", "for RTR1"
            r"\bof\s+([A-Z0-9_-]+)",  # "of SW1", "of RTR1"
            r"^([A-Z0-9_-]+)\s+",  # "SW1 show vlans" (device at start)
        ]

        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                device_name = match.group(1).upper()

                # Check if this device exists in inventory
                if self.inventory_manager and device_name in self.inventory_manager:
                    # Remove the device reference from question
                    cleaned_question = re.sub(
                        pattern, " ", question, flags=re.IGNORECASE
                    ).strip()

                    # Clean up extra spaces
                    cleaned_question = " ".join(cleaned_question.split())

                    logger.debug(
                        f"Extracted device: {device_name}, "
                        f"cleaned question: {cleaned_question}"
                    )

                    return device_name, cleaned_question

        return None, question

    def route_to_device(self, device_name: str) -> bool:
        """Route to a device by name from inventory.

        Args:
            device_name: Name of device in inventory

        Returns:
            True if routed successfully
        """
        # Get device from inventory
        device_info = self.inventory_manager.get_device(device_name)

        if not device_info:
            logger.warning(f"Device '{device_name}' not found in inventory")
            return False

        # Check if device is already connected
        if self.device_manager.is_connected(device_name):
            # Just switch to it
            try:
                self.device_manager.switch_device(device_name)
                logger.info(f"Switched to existing device '{device_name}'")
                return True
            except ValueError as e:
                logger.warning(f"Could not switch to '{device_name}': {e}")
                return False

        # Device not connected, connect to it
        try:
            logger.info(
                f"Connecting to '{device_name}' ({device_info.hostname})..."
            )
            success = self.device_manager.connect_to_device(device_name, device_info)
            if success:
                logger.info(f"✓ Connected to {device_name}")
            else:
                logger.error(f"Failed to connect to {device_name}")
            return success
        except Exception as e:
            logger.error(f"Error connecting to {device_name}: {e}")
            return False