"""Core components package for the Simplified AI Network Agent.

This package contains the fundamental building blocks of the network management system:
- NetworkManager: Handles device connections and command execution using Nornir
- Config: Centralized application settings and configuration management
- Models: Pydantic models for structured data contracts
"""

from .network_manager import NetworkManager

__all__ = ["NetworkManager"]

