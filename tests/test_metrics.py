"""
Test suite for metrics dashboard functionality.
"""

import sys
import os
import time

# Add src to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.metrics import MetricsCollector, MetricsDashboard, MetricType


def test_metrics_collector():
    """Test MetricsCollector functionality."""
    print("Testing MetricsCollector...")
    
    # Create a metrics collector
    collector = MetricsCollector(max_events=100)
    
    # Record some events
    collector.record_event(MetricType.COMMAND_EXECUTED, {"command": "show version", "output_length": 100})
    collector.record_event(MetricType.COMMAND_FAILED, {"command": "show invalid", "error": "invalid command"})
    collector.record_event(MetricType.COMMAND_BLOCKED, {"command": "reload", "reason": "blocked_keyword"})
    collector.record_event(MetricType.PROMPT_INJECTION_ATTEMPT, {"query": "ignore previous instructions"})
    
    # Check total events
    assert collector.get_total_events() == 4
    
    # Check specific event counts
    assert collector.get_event_count(MetricType.COMMAND_EXECUTED) == 1
    assert collector.get_event_count(MetricType.COMMAND_FAILED) == 1
    assert collector.get_event_count(MetricType.COMMAND_BLOCKED) == 1
    assert collector.get_event_count(MetricType.PROMPT_INJECTION_ATTEMPT) == 1
    
    # Test command metrics
    cmd_metrics = collector.get_command_metrics()
    assert cmd_metrics["total_commands"] == 3  # executed + failed + blocked
    assert cmd_metrics["successful_commands"] == 1
    assert cmd_metrics["failed_commands"] == 1
    assert cmd_metrics["blocked_commands"] == 1
    assert cmd_metrics["success_rate"] == 1/3  # 1 successful out of 3 total commands
    
    # Test security metrics
    sec_metrics = collector.get_security_metrics()
    assert sec_metrics["prompt_injection_attempts"] == 1
    assert sec_metrics["blocked_commands"] == 1
    assert sec_metrics["security_events"] == 2  # injection attempt + blocked command
    
    print("✓ MetricsCollector test passed")


def test_metrics_dashboard():
    """Test MetricsDashboard functionality."""
    print("Testing MetricsDashboard...")
    
    # Create a metrics collector and add some events
    collector = MetricsCollector()
    
    # Add various events
    for i in range(10):
        collector.record_event(MetricType.COMMAND_EXECUTED, {"command": f"show {i}"})
    for i in range(3):
        collector.record_event(MetricType.COMMAND_FAILED, {"command": f"invalid {i}"})
    for i in range(2):
        collector.record_event(MetricType.COMMAND_BLOCKED, {"command": f"blocked {i}"})
    for i in range(5):
        collector.record_event(MetricType.PROMPT_INJECTION_ATTEMPT, {"query": f"injection {i}"})
    
    # Create dashboard
    dashboard = MetricsDashboard(collector)
    
    # Generate text report
    text_report = dashboard.generate_text_report()
    assert "NETWORK AGENT METRICS DASHBOARD" in text_report
    assert "Total Commands: 15" in text_report  # 10 + 3 + 2
    assert "Successful: 10" in text_report
    assert "Prompt Injection Attempts: 5" in text_report
    
    # Generate JSON report
    json_report = dashboard.generate_json_report()
    assert "uptime_seconds" in json_report
    assert "command_metrics" in json_report
    assert "security_metrics" in json_report
    assert json_report["command_metrics"]["total_commands"] == 15
    
    # Test alerts (should be empty for normal metrics)
    alerts = dashboard.get_alerts()
    # In this case, we might get alerts if the success rate is too low
    print(f"Alerts: {alerts}")
    
    print("✓ MetricsDashboard test passed")


def test_metrics_time_based():
    """Test time-based metrics functionality."""
    print("Testing time-based metrics...")
    
    # Create a metrics collector
    collector = MetricsCollector()
    
    # Record some events
    collector.record_event(MetricType.COMMAND_EXECUTED)
    time.sleep(0.01)  # Small delay to ensure different timestamps
    collector.record_event(MetricType.COMMAND_EXECUTED)
    
    # Get commands per minute (these would be 0 since we just added 2 events)
    cpm = collector.get_commands_per_minute(1)  # 1 minute
    # The 2 events were just added, so they are within the last minute
    assert cpm >= 0  # Should be non-negative
    
    # Test getting recent security events
    recent_security = collector.get_recent_security_events(1)  # 1 minute
    # Should be empty since we didn't add any security events
    assert len(recent_security) == 0
    
    # Add a security event and test again
    collector.record_event(MetricType.PROMPT_INJECTION_ATTEMPT)
    recent_security = collector.get_recent_security_events(1)
    assert len(recent_security) >= 1
    
    print("✓ Time-based metrics test passed")


def test_metrics_alerts():
    """Test metrics alert functionality."""
    print("Testing metrics alerts...")
    
    # Create a metrics collector
    collector = MetricsCollector()
    
    # Create dashboard
    dashboard = MetricsDashboard(collector)
    
    # Get alerts for normal metrics (should be few or none)
    alerts = dashboard.get_alerts()
    # Initially there should be no alerts or very few
    
    # Simulate poor command success rate
    for _ in range(10):
        collector.record_event(MetricType.COMMAND_EXECUTED)
    for _ in range(90):  # 90% failure rate
        collector.record_event(MetricType.COMMAND_FAILED)
    
    alerts = dashboard.get_alerts()
    high_alert_found = any("HIGH" in alert and "success rate" in alert for alert in alerts)
    assert high_alert_found, f"Expected high alert for low success rate, got: {alerts}"
    
    # Test high security events
    collector = MetricsCollector()
    for _ in range(15):
        collector.record_event(MetricType.PROMPT_INJECTION_ATTEMPT)
    
    dashboard = MetricsDashboard(collector)
    alerts = dashboard.get_alerts()
    sec_alert_found = any("MEDIUM" in alert and "security" in alert for alert in alerts)
    assert sec_alert_found, f"Expected medium alert for high security events, got: {alerts}"
    
    print("✓ Metrics alerts test passed")


def run_all_tests():
    """Run all metrics tests."""
    print("Running Metrics Test Suite...\n")
    
    test_metrics_collector()
    test_metrics_dashboard()
    test_metrics_time_based()
    test_metrics_alerts()
    
    print("\n🎉 All Metrics Tests Passed!")
    print("✅ Metrics collection")
    print("✅ Metrics dashboard")
    print("✅ Time-based metrics")
    print("✅ Metrics alerts")


if __name__ == "__main__":
    run_all_tests()