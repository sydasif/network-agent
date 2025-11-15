"""
Test suite for health check functionality.
"""

import sys
import os
from unittest.mock import Mock

# Add src to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.health import HealthStatus, health_check, is_system_healthy
from src.network_device import DeviceConnection
from src.agent import Agent
from src.audit import AuditLogger


def test_health_status():
    """Test HealthStatus class functionality."""
    print("Testing HealthStatus class...")
    
    # Create mock objects
    mock_device = Mock(spec=DeviceConnection)
    mock_device.get_connection_status.return_value = {
        "state": "connected",
        "is_alive": True,
        "connected": True,
        "uptime_seconds": 3600
    }
    mock_device.connection_attempts = 1
    mock_device.last_connection_attempt = "2023-01-01T00:00:00"
    
    # Mock agent
    mock_agent = Mock(spec=Agent)
    mock_agent.current_model = "llama-3.3-70b-versatile"
    mock_agent.is_active = True
    mock_agent.last_query_time = "2023-01-01T00:00:00"
    mock_agent.model_fallback_count = 0
    mock_agent.rate_limit_used = 5
    mock_agent.total_commands = 10
    mock_agent.successful_commands = 9
    mock_agent.last_command_time = "2023-01-01T00:00:00"
    
    # Create health status instance
    health_status = HealthStatus(mock_device, mock_agent)
    
    # Get health status
    result = health_status.get_health_status()
    
    # Verify structure
    assert "timestamp" in result
    assert "connection" in result
    assert "agent" in result
    assert "commands" in result
    assert "system" in result
    
    # Verify connection section
    conn = result["connection"]
    assert conn["state"] == "connected"
    assert conn["alive"] is True
    assert conn["connected"] is True
    
    # Verify agent section
    agent_info = result["agent"]
    assert agent_info["model"] == "llama-3.3-70b-versatile"
    assert agent_info["active"] is True
    
    # Verify command stats
    cmd_stats = result["commands"]
    assert cmd_stats["total"] == 10
    assert cmd_stats["successful"] == 9
    assert cmd_stats["success_rate"] == 0.9
    
    print("✓ HealthStatus class test passed")


def test_health_check_function():
    """Test health_check convenience function."""
    print("Testing health_check function...")
    
    # Create mock objects
    mock_device = Mock(spec=DeviceConnection)
    mock_device.get_connection_status.return_value = {
        "state": "connected",
        "is_alive": True,
        "connected": True,
        "uptime_seconds": 1800
    }
    
    mock_agent = Mock(spec=Agent)
    mock_agent.current_model = "openai/gpt-oss-120b"
    mock_agent.is_active = True
    mock_agent.total_commands = 5
    mock_agent.successful_commands = 5
    
    # Call health check function
    result = health_check(mock_device, mock_agent)
    
    # Verify it returns a dictionary with expected keys
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "connection" in result
    assert "agent" in result
    assert "commands" in result
    assert "system" in result
    
    print("✓ health_check function test passed")


def test_is_system_healthy():
    """Test is_system_healthy function."""
    print("Testing is_system_healthy function...")
    
    # Create mock objects for healthy system
    mock_device_healthy = Mock(spec=DeviceConnection)
    mock_device_healthy.get_connection_status.return_value = {
        "state": "connected",  # Healthy state
        "is_alive": True,
        "connected": True,
        "uptime_seconds": 1200
    }
    
    mock_agent_healthy = Mock(spec=Agent)
    mock_agent_healthy.is_active = True
    
    # Test healthy system
    result = is_system_healthy(mock_device_healthy, mock_agent_healthy)
    assert result is True
    
    # Create mock objects for unhealthy system
    mock_device_unhealthy = Mock(spec=DeviceConnection)
    mock_device_unhealthy.get_connection_status.return_value = {
        "state": "disconnected",  # Unhealthy state
        "is_alive": False,
        "connected": False,
        "uptime_seconds": 0
    }
    
    # Test unhealthy system
    result = is_system_healthy(mock_device_unhealthy, mock_agent_healthy)
    assert result is False
    
    # Test with inactive agent
    mock_agent_inactive = Mock(spec=Agent)
    mock_agent_inactive.is_active = False
    
    result = is_system_healthy(mock_device_healthy, mock_agent_inactive)
    assert result is False
    
    print("✓ is_system_healthy function test passed")


def run_all_tests():
    """Run all health check tests."""
    print("Running Health Check Test Suite...\n")
    
    test_health_status()
    test_health_check_function()
    test_is_system_healthy()
    
    print("\n🎉 All Health Check Tests Passed!")
    print("✅ HealthStatus class")
    print("✅ health_check function")
    print("✅ is_system_healthy function")


if __name__ == "__main__":
    run_all_tests()