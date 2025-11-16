"""
Health check endpoint for system monitoring.

Provides comprehensive health status of the network agent system.
"""

from typing import Dict, Any
from datetime import datetime
import time

from .network_device import DeviceConnection
from .agent import Agent
from .audit import AuditLogger


class HealthStatus:
    """Health status information for the system."""

    def __init__(self, device: DeviceConnection, agent: Agent, audit_logger: AuditLogger = None):
        """Initialize health status checker.

        Args:
            device: Device connection instance
            agent: Agent instance
            audit_logger: Optional audit logger instance
        """
        self.device = device
        self.agent = agent
        self.audit_logger = audit_logger

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive system health status.

        Returns:
            Dictionary containing health status information
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "connection": self._get_connection_status(),
            "agent": self._get_agent_status(),
            "system": self._get_system_info(),
        }

    def _get_connection_status(self) -> Dict[str, Any]:
        """Get device connection status information.

        Returns:
            Dictionary with connection health information
        """
        connection_status = self.device.get_connection_status()

        return {
            "state": connection_status.get("state", "unknown"),
            "alive": connection_status.get("is_alive", False),
            "connected": connection_status.get("connected", False),
        }

    def _get_agent_status(self) -> Dict[str, Any]:
        """Get agent status information.

        Returns:
            Dictionary with agent health information
        """
        return {
            "model": getattr(self.agent, 'model_name', 'unknown'),
            "active": getattr(self.agent, 'is_active', True),
            "last_query_time": getattr(self.agent, 'last_query_time', None),
        }

    def _get_system_info(self) -> Dict[str, Any]:
        """Get general system information.

        Returns:
            Dictionary with system information
        """
        return {
            "health_check_time": time.time(),
            "version": "1.0.0",  # This could be dynamically loaded from a version file
            "status": "healthy",  # Overall system status
        }


def health_check(device: DeviceConnection, agent: Agent, audit_logger: AuditLogger = None) -> dict:
    """Get system health status (convenience function).

    Args:
        device: DeviceConnection instance
        agent: Agent instance
        audit_logger: Optional AuditLogger instance

    Returns:
        Health status dictionary
    """
    health_status = HealthStatus(device, agent, audit_logger)
    return health_status.get_health_status()


def is_system_healthy(device: DeviceConnection, agent: Agent) -> bool:
    """Check if the system is in a healthy state.

    Args:
        device: DeviceConnection instance
        agent: Agent instance

    Returns:
        True if system is healthy, False otherwise
    """
    health_status = health_check(device, agent)

    # Determine if system is healthy based on key metrics
    connection_healthy = health_status["connection"]["state"] == "connected"
    agent_active = health_status["agent"]["active"]

    return connection_healthy and agent_active