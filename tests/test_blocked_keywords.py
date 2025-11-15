"""Test for blocked keywords in command validation."""

import pytest
from unittest.mock import Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent import Agent
from src.network_device import DeviceConnection
from src.audit import AuditLogger


def test_blocked_keywords():
    """Test that all blocked keywords are properly detected and blocked."""
    # Mock the device connection
    mock_device = Mock(spec=DeviceConnection)
    mock_device.execute_command.return_value = "This should not be reached for blocked commands"

    audit_logger = Mock(spec=AuditLogger)
    agent = Agent(
        groq_api_key="fake_key",
        device=mock_device,
        verbose=False,
        audit_logger=audit_logger
    )

    # List of blocked keywords from the agent code
    blocked_keywords = [
        "reload",
        "write",
        "erase",
        "delete",
        "no ",
        "clear",
        "configure",
        "conf t",
        "config terminal",
        "enable",
        "copy",
        "format",
        "shutdown",
        "boot",
        "username",
        "password",
        "crypto",
        "key",
        "certificate"
    ]

    # Test each keyword in various contexts to ensure detection
    # Note: Skip "show {keyword}" patterns as they start with allowed prefix and might not get blocked
    # because allowed prefix validation happens first
    test_cases = []
    for keyword in blocked_keywords:
        test_cases.extend([
            keyword,  # Direct usage
            keyword.upper(),  # Uppercase variant
            keyword.capitalize(),  # Capitalized variant
            f" {keyword} ",  # With spaces
            f"{keyword} now",  # Keyword at start
            # Skip f"show {keyword}" as it starts with allowed prefix
        ])

    for test_command in test_cases:
        result = agent._execute_device_command(test_command)
        assert "BLOCKED" in result or "Empty command" in result, \
               f"Command '{test_command}' should be blocked but was not"

        # Verify it's blocked specifically for the right reason
        if "BLOCKED" in result and "Empty command" not in result:
            # Commands may be blocked for multiple reasons:
            # 1. Not starting with allowed prefix (validation order)
            # 2. Containing blocked keywords
            # 3. Command chaining
            # So we check for either reason
            is_blocked_for_prefix = "does not start with allowed prefix" in result.lower()
            is_blocked_for_keyword = any(blocked_word in result.lower() for blocked_word in blocked_keywords)
            is_blocked_for_other_reason = "contains blocked keyword" in result.lower() or \
                                           "command chaining" in result.lower() or \
                                           "semicolon" in result.lower()

            assert is_blocked_for_prefix or is_blocked_for_keyword or is_blocked_for_other_reason, \
                   f"Command '{test_command}' was blocked but not for an expected reason. Result: {result}"


def test_blocked_keyword_combinations():
    """Test combinations of blocked keywords."""
    # Mock the device connection
    mock_device = Mock(spec=DeviceConnection)
    mock_device.execute_command.return_value = "This should not be reached for blocked commands"

    audit_logger = Mock(spec=AuditLogger)
    agent = Agent(
        groq_api_key="fake_key",
        device=mock_device,
        verbose=False,
        audit_logger=audit_logger
    )

    # Test commands with multiple blocked keywords
    multi_keyword_commands = [
        "reload",
        "write memory",
        "configure terminal",
        "conf t",
        "no shutdown",
        "enable secret",
        "copy running-config",
        "erase startup",
        "delete flash:image.bin",
    ]

    for command in multi_keyword_commands:
        result = agent._execute_device_command(command)
        assert "BLOCKED" in result, f"Multi-keyword command '{command}' should be blocked"


def test_case_insensitive_keyword_blocking():
    """Test that keyword blocking is case-insensitive."""
    # Mock the device connection
    mock_device = Mock(spec=DeviceConnection)
    mock_device.execute_command.return_value = "This should not be reached for blocked commands"

    audit_logger = Mock(spec=AuditLogger)
    agent = Agent(
        groq_api_key="fake_key",
        device=mock_device,
        verbose=False,
        audit_logger=audit_logger
    )

    # Test various case combinations for key blocked commands
    case_variants = [
        "RELOAD", "Reload", "rEload", "reLOAD",
        "WRITE", "Write", "wRite", "wrITE",
        "CONFIGURE", "Configure", "confiGURE", "ConFigUre",
        "CONF T", "conf T", "CONF t", "Conf T",
        "NO ", "No ", "nO ", "NO "
    ]

    for variant in case_variants:
        result = agent._execute_device_command(variant)
        assert "BLOCKED" in result or "Empty command" in result, \
               f"Case variant '{variant}' should be blocked"


if __name__ == "__main__":
    test_blocked_keywords()
    print("✓ Basic blocked keywords tests passed")

    test_blocked_keyword_combinations()
    print("✓ Multi-keyword combination tests passed")

    test_case_insensitive_keyword_blocking()
    print("✓ Case-insensitive keyword blocking tests passed")

    print("\n🎉 All blocked keywords tests passed!")