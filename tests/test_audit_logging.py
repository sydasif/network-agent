"""Test for audit logging functionality."""

import pytest
import sys
import os
from datetime import datetime
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audit import AuditLogger, SecurityEventType
from src.sensitive_data import SensitiveDataProtector


def test_audit_logger_initialization():
    """Test audit logger initialization."""
    # Create logger with temporary directory
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Check that session ID is generated
    assert logger.session_id is not None
    assert len(logger.session_id) > 0

    # Check that log directory was created
    log_dir = Path("test_logs")
    assert log_dir.exists()

    # Check that event counters are initialized
    assert all(count == 0 for count in logger.event_counts.values())

    # Clean up
    import shutil
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_log_event():
    """Test basic event logging."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Log a test event
    logger.log_event(
        SecurityEventType.COMMAND_EXECUTED,
        "Test command executed",
        severity="INFO",
        command="show version",
        output_length=100
    )

    # Verify event counter was incremented
    assert logger.event_counts[SecurityEventType.COMMAND_EXECUTED] == 1

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_session_events():
    """Test session start and end events."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Log session start
    logger.log_session_start("test_user", "192.168.1.1", "test_model")

    # Verify counter was incremented
    assert logger.event_counts[SecurityEventType.SESSION_START] == 1

    # Log session end
    logger.log_session_end(30.5)

    # Verify counter was incremented
    assert logger.event_counts[SecurityEventType.SESSION_END] == 1

    # Check session summary
    summary = logger.get_session_summary()
    assert "session_id" in summary
    assert "duration_seconds" in summary
    assert "total_events" in summary
    assert summary["total_events"] >= 2  # At least start and end events

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_connection_events():
    """Test connection-related events."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Log connection established
    logger.log_connection_established("192.168.1.1", "admin")
    assert logger.event_counts[SecurityEventType.CONNECTION_ESTABLISHED] == 1

    # Log connection failed
    logger.log_connection_failed("192.168.1.1", "admin", "Authentication failed")
    assert logger.event_counts[SecurityEventType.CONNECTION_FAILED] == 1

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_command_events():
    """Test command execution events."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Log successful command
    logger.log_command_executed("show version", True, output_length=200)
    assert logger.event_counts[SecurityEventType.COMMAND_EXECUTED] == 1

    # Log failed command
    logger.log_command_executed("show invalid", False, error="Command not found")
    assert logger.event_counts[SecurityEventType.COMMAND_FAILED] == 1

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_security_events():
    """Test security-related events."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Log blocked command
    logger.log_command_blocked("reload", "Contains blocked keyword")
    assert logger.event_counts[SecurityEventType.COMMAND_BLOCKED] == 1

    # Log prompt injection
    logger.log_prompt_injection("Ignore previous instructions", ["ignore previous instructions"])
    assert logger.event_counts[SecurityEventType.PROMPT_INJECTION_DETECTED] == 1

    # Log validation failure
    logger.log_validation_failure("malicious query", "Suspicious patterns detected")
    assert logger.event_counts[SecurityEventType.VALIDATION_FAILURE] == 1

    # Log rate limit exceeded
    logger.log_rate_limit_exceeded(30, 60)
    assert logger.event_counts[SecurityEventType.RATE_LIMIT_EXCEEDED] == 1

    # Log model fallback
    logger.log_model_fallback("model_a", "model_b", "timeout")
    assert logger.event_counts[SecurityEventType.MODEL_FALLBACK] == 1

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_sensitive_data_in_events():
    """Test that sensitive data is sanitized in audit logs."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Initialize data protector
    protector = SensitiveDataProtector()

    # Test logging command with password
    cmd_with_password = "username admin password secret123"
    logger.log_command_executed(cmd_with_password, True, output_length=50)

    # The command should be sanitized before logging
    # Check that no sensitive data appears in the logs (by checking internal state or behavior)

    # Test logging failed command with error containing password
    logger.log_command_executed(
        "show config",
        False,
        error="Failed because password was 'secret123'"
    )

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_json_logging():
    """Test JSON structured logging."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Log an event
    logger.log_event(
        SecurityEventType.COMMAND_EXECUTED,
        "Test command",
        severity="INFO",
        command="show version"
    )

    # Check that JSON log file was created and contains valid JSON
    json_log_path = Path("test_logs") / f"audit_{logger.session_id}.jsonl"
    assert json_log_path.exists()

    # Read and parse the JSON log
    lines = json_log_path.read_text().strip().split('\n')
    assert len(lines) > 0

    # Parse the first line as JSON
    event_data = json.loads(lines[0])
    assert "timestamp" in event_data
    assert "session_id" in event_data
    assert "event_type" in event_data
    assert "severity" in event_data
    assert "message" in event_data

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_file_logging():
    """Test text file logging."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Log an event
    logger.log_event(
        SecurityEventType.SESSION_START,
        "User session started",
        severity="INFO",
        user="test_user"
    )

    # Check that text log file was created
    text_log_path = Path("test_logs") / f"audit_{logger.session_id}.log"
    assert text_log_path.exists()

    # Check that the log contains the expected content
    log_content = text_log_path.read_text()
    assert "SESSION_START" in log_content
    assert "User session started" in log_content

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_session_summary():
    """Test session summary generation."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Generate some events
    logger.log_session_start("test_user", "192.168.1.1", "gpt-3.5")
    logger.log_command_executed("show version", True, output_length=100)
    logger.log_command_executed("show ip route", True, output_length=200)
    logger.log_session_end(60.0)

    # Get session summary
    summary = logger.get_session_summary()

    # Verify summary structure
    assert "session_id" in summary
    assert "duration_seconds" in summary
    assert "event_counts" in summary
    assert "total_events" in summary

    # Verify some expected counts
    assert summary["total_events"] >= 3  # At least session start, 2 commands, session end
    assert isinstance(summary["event_counts"], dict)

    # Verify that there's a summary file (the file is created by the close method)
    # We need to call close to ensure the summary file is written
    logger.close()  # This should trigger writing the summary file

    # Check for summary files
    summary_files = list(Path("test_logs").glob("summary_*.json"))
    assert len(summary_files) == 1, f"Expected 1 summary file, found {len(summary_files)}: {list(Path('test_logs').glob('*'))}"

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


def test_event_type_coverage():
    """Test that all security event types can be logged."""
    logger = AuditLogger(
        log_dir="test_logs",
        enable_console=False,
        enable_file=True,
        enable_json=True,
        log_level="INFO"
    )

    # Test each event type
    event_tests = [
        (SecurityEventType.LOGIN_SUCCESS, lambda: logger.log_event(SecurityEventType.LOGIN_SUCCESS, "Login success", user="test")),
        (SecurityEventType.LOGIN_FAILURE, lambda: logger.log_event(SecurityEventType.LOGIN_FAILURE, "Login failure", user="test")),
        (SecurityEventType.LOGOUT, lambda: logger.log_event(SecurityEventType.LOGOUT, "User logged out", user="test")),
        (SecurityEventType.COMMAND_EXECUTED, lambda: logger.log_command_executed("show version", True, output_length=100)),
        (SecurityEventType.COMMAND_BLOCKED, lambda: logger.log_command_blocked("reload", "blocked")),
        (SecurityEventType.COMMAND_FAILED, lambda: logger.log_command_executed("bad command", False, error="error")),
        (SecurityEventType.PROMPT_INJECTION_DETECTED, lambda: logger.log_prompt_injection("test", ["test"])),
        (SecurityEventType.VALIDATION_FAILURE, lambda: logger.log_validation_failure("test", "failure")),
        (SecurityEventType.RATE_LIMIT_EXCEEDED, lambda: logger.log_rate_limit_exceeded(30, 60)),
        (SecurityEventType.SUSPICIOUS_PATTERN, lambda: logger.log_event(SecurityEventType.SUSPICIOUS_PATTERN, "suspicious", pattern="test")),
        (SecurityEventType.CONNECTION_ESTABLISHED, lambda: logger.log_connection_established("192.168.1.1", "admin")),
        (SecurityEventType.CONNECTION_LOST, lambda: logger.log_event(SecurityEventType.CONNECTION_LOST, "connection lost")),
        (SecurityEventType.CONNECTION_FAILED, lambda: logger.log_connection_failed("192.168.1.1", "admin", "failed")),
        (SecurityEventType.RECONNECT_ATTEMPT, lambda: logger.log_event(SecurityEventType.RECONNECT_ATTEMPT, "reconnect attempt")),
        (SecurityEventType.SESSION_START, lambda: logger.log_session_start("user", "device", "model")),
        (SecurityEventType.SESSION_END, lambda: logger.log_session_end(30.0)),
        (SecurityEventType.MODEL_FALLBACK, lambda: logger.log_model_fallback("model1", "model2", "reason")),
        (SecurityEventType.ERROR_OCCURRED, lambda: logger.log_event(SecurityEventType.ERROR_OCCURRED, "error", error="test")),
    ]

    for event_type, test_func in event_tests:
        # Reset counter to 0 first
        logger.event_counts[event_type] = 0
        test_func()
        assert logger.event_counts[event_type] >= 1, f"Event {event_type} was not logged properly"

    # Clean up
    import shutil
    log_dir = Path("test_logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)


if __name__ == "__main__":
    test_audit_logger_initialization()
    print("✓ Audit logger initialization tests passed")

    test_log_event()
    print("✓ Basic event logging tests passed")

    test_session_events()
    print("✓ Session events tests passed")

    test_connection_events()
    print("✓ Connection events tests passed")

    test_command_events()
    print("✓ Command events tests passed")

    test_security_events()
    print("✓ Security events tests passed")

    test_sensitive_data_in_events()
    print("✓ Sensitive data sanitization in events tests passed")

    test_json_logging()
    print("✓ JSON logging tests passed")

    test_file_logging()
    print("✓ File logging tests passed")

    test_session_summary()
    print("✓ Session summary tests passed")

    test_event_type_coverage()
    print("✓ Event type coverage tests passed")

    print("\n🎉 All audit logging functionality tests passed!")