"""Core components package for the AI Network Agent.

This package contains the fundamental building blocks of the network management system:
- NetworkManager: Handles device inventory, connections, and command execution
- Device: Data model representing a network device with connection details
- Config: Centralized application settings and configuration management
- Models: Pydantic models for structured data contracts
- StateManager: Persistent storage for device state snapshots
"""

from .network_manager import NetworkManager, Device

__all__ = ["Device", "NetworkManager"]
