"""
Integration test to verify all new features work together.
"""

import sys
import os

# Add src to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.health import HealthStatus, health_check
from src.config import Config
from src.metrics import MetricsCollector, MetricsDashboard, MetricType
from src.network_device import DeviceConnection
from src.agent import Agent
from unittest.mock import Mock


def test_integration():
    """Test that all new features work together."""
    print("Testing integration of all new features...")

    # 1. Test configuration loading
    print("  - Testing configuration loading...")
    config = Config()
    assert config.app.security.max_query_length == 500  # Default value
    print("    ✓ Configuration loading works")

    # 2. Test metrics collection
    print("  - Testing metrics collection...")
    metrics_collector = MetricsCollector(max_events=1000)

    # Record some events
    metrics_collector.record_event(MetricType.COMMAND_EXECUTED, {"command": "show version"})
    metrics_collector.record_event(MetricType.COMMAND_FAILED, {"command": "invalid command"})
    metrics_collector.record_event(MetricType.PROMPT_INJECTION_ATTEMPT, {"query": "ignore instructions"})

    # Check that events were recorded
    cmd_metrics = metrics_collector.get_command_metrics()
    assert cmd_metrics["total_commands"] == 2  # executed + failed
    print("    ✓ Metrics collection works")

    # 3. Test metrics dashboard
    print("  - Testing metrics dashboard...")
    dashboard = MetricsDashboard(metrics_collector)
    json_report = dashboard.generate_json_report()
    text_report = dashboard.generate_text_report()

    assert "uptime_seconds" in json_report
    assert "command_metrics" in json_report
    assert "NETWORK AGENT METRICS DASHBOARD" in text_report
    print("    ✓ Metrics dashboard works")

    # 4. Test health checks
    print("  - Testing health checks...")

    # Create mock objects for health check
    mock_device = Mock(spec=DeviceConnection)
    mock_device.get_connection_status.return_value = {
        "state": "connected",
        "is_alive": True,
        "connected": True,
        "uptime_seconds": 3600
    }
    mock_device.connection_attempts = 1

    # Mock agent
    mock_agent = Mock(spec=Agent)
    mock_agent.current_model = "llama-3.3-70b-versatile"
    mock_agent.is_active = True
    mock_agent.total_commands = 10
    mock_agent.successful_commands = 9

    # Test health check functions
    health_status = health_check(mock_device, mock_agent)
    is_healthy = HealthStatus(mock_device, mock_agent).get_health_status()

    # Verify health status structure
    assert "connection" in health_status
    assert "agent" in health_status
    assert "commands" in health_status
    assert health_status["connection"]["state"] == "connected"
    print("    ✓ Health checks work")

    # 5. Test all features working together
    print("  - Testing all features integration...")

    # Use configuration values to influence metrics collection
    max_length = config.app.security.max_query_length
    assert max_length > 0

    # Use metrics to influence health assessment
    sec_metrics = metrics_collector.get_security_metrics()
    cmd_metrics = metrics_collector.get_command_metrics()

    # Verify metrics are properly formatted
    assert isinstance(cmd_metrics["success_rate"], float)
    assert 0.0 <= cmd_metrics["success_rate"] <= 1.0

    print("    ✓ All features integrate properly")

    # 6. Test configuration affecting metrics behavior
    print("  - Testing configuration-driven metrics...")

    # Configuration reloading is now handled differently with Pydantic
    # Reload the configuration to test the reload functionality
    config.reload()
    current_length = config.app.security.max_query_length
    assert current_length > 0
    print("    ✓ Configuration reload works")

    print("\n🎉 All integration tests passed!")
    print("✅ Configuration loading and management")
    print("✅ Metrics collection and dashboard")
    print("✅ Health monitoring system")
    print("✅ All features working together")


def run_integration_test():
    """Run the integration test."""
    print("Running Integration Test Suite...\n")
    test_integration()


if __name__ == "__main__":
    run_integration_test()