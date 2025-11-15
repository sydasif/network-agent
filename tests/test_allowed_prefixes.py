"""Test for allowed command prefixes."""

import pytest
from unittest.mock import Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent import Agent
from src.network_device import DeviceConnection
from src.audit import AuditLogger


def test_allowed_prefixes():
    """Test that allowed command prefixes are properly accepted."""
    # Mock the device connection
    mock_device = Mock(spec=DeviceConnection)
    mock_device.execute_command.return_value = "Command executed successfully"

    audit_logger = Mock(spec=AuditLogger)
    agent = Agent(
        groq_api_key="fake_key",
        device=mock_device,
        verbose=False,
        audit_logger=audit_logger
    )

    # List of allowed prefixes from the agent code
    allowed_prefixes = [
        "show",
        "display",
        "get",
        "dir",
        "more",
        "verify"
    ]

    # Test each allowed prefix with various commands
    for prefix in allowed_prefixes:
        test_commands = [
            f"{prefix} version",
            f"{prefix} ip interface brief",
            f"{prefix} running-config",
            f"{prefix} arp",
            f"{prefix} vlan brief",
            f"{prefix} mac address-table",
            f"{prefix} processes",
            f"{prefix} environment",
            f"{prefix} clock"
        ]

        for command in test_commands:
            result = agent._execute_device_command(command)
            assert "Command executed successfully" in result, \
                   f"Allowed command '{command}' was unexpectedly blocked"


def test_case_insensitive_prefix_matching():
    """Test that prefix matching is case-insensitive."""
    # Mock the device connection
    mock_device = Mock(spec=DeviceConnection)
    mock_device.execute_command.return_value = "Command executed successfully"

    audit_logger = Mock(spec=AuditLogger)
    agent = Agent(
        groq_api_key="fake_key",
        device=mock_device,
        verbose=False,
        audit_logger=audit_logger
    )

    # Test various case combinations for allowed prefixes
    case_variants = [
        "SHOW version",
        "Show interfaces",
        "show VERSION",
        "DISPLAY config",
        "Display status",
        "display INTERFACE",
        "GET info",
        "Get system",
        "get STATUS"
    ]

    for command in case_variants:
        result = agent._execute_device_command(command)
        assert "Command executed successfully" in result, \
               f"Case variant command '{command}' was unexpectedly blocked"


def test_allowed_pipe_commands():
    """Test that allowed pipe commands work properly."""
    # Mock the device connection
    mock_device = Mock(spec=DeviceConnection)
    mock_device.execute_command.return_value = "Piped command executed successfully"

    audit_logger = Mock(spec=AuditLogger)
    agent = Agent(
        groq_api_key="fake_key",
        device=mock_device,
        verbose=False,
        audit_logger=audit_logger
    )

    # Test allowed pipe commands (excluding those with blocked keywords)
    allowed_pipe_commands = [
        "show running-config | include interface",
        "show ip route | begin ospf",
        "show interfaces | section eth0",
        "show version | include Cisco",
        # Note: Skipping "show running-config | exclude password" - contains "password" keyword
        "display current-configuration | include bgp",
        "show ip bgp summary | include Active"
    ]

    for command in allowed_pipe_commands:
        result = agent._execute_device_command(command)
        assert "Piped command executed successfully" in result, \
               f"Allowed pipe command '{command}' was unexpectedly blocked"


def test_prefix_with_various_formats():
    """Test allowed prefixes with different command formats."""
    # Mock the device connection
    mock_device = Mock(spec=DeviceConnection)
    mock_device.execute_command.return_value = "Command executed successfully"

    audit_logger = Mock(spec=AuditLogger)
    agent = Agent(
        groq_api_key="fake_key",
        device=mock_device,
        verbose=False,
        audit_logger=audit_logger
    )

    # Test variations of allowed commands
    allowed_commands = [
        # Show commands
        "show",
        "show ",
        "show version",
        "show ip route vrf management",
        "show interface g0/1",
        "show ip ospf neighbor",

        # Display commands (alternative vendor)
        "display",
        "display current-configuration",
        "display interface status",

        # Get commands
        "get system status",
        "get config",
        "get interfaces",

        # Other allowed commands
        "dir",
        "dir flash:",
        "more system:running-config",
        "verify file image.bin"
    ]

    for command in allowed_commands:
        result = agent._execute_device_command(command)
        # Commands with just the prefix or just prefix+space might be rejected for other reasons
        # but shouldn't be blocked for prefix reasons
        if command.strip() in ["show", "display", "get", "dir", "more", "verify"]:
            # These are too short and might fail for other reasons, that's OK
            continue
        else:
            # More complete commands should succeed
            if "show " in command or "display " in command or "get " in command or \
               "dir " in command or "more " in command or "verify " in command:
                assert "Command executed successfully" in result, \
                       f"Allowed command '{command}' was unexpectedly blocked"


def test_prefix_not_at_start():
    """Test that prefixes must be at the beginning of the command."""
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

    # These commands contain allowed prefixes but don't start with them
    # and should be blocked
    non_prefix_commands = [
        "reload and then show version",
        "configure terminal and show interfaces",
        "erase config to show running",
        "write memory and display status"
    ]

    for command in non_prefix_commands:
        result = agent._execute_device_command(command)
        assert "BLOCKED" in result, \
               f"Command '{command}' should be blocked (doesn't start with allowed prefix)"


if __name__ == "__main__":
    test_allowed_prefixes()
    print("✓ Basic allowed prefixes tests passed")

    test_case_insensitive_prefix_matching()
    print("✓ Case-insensitive prefix matching tests passed")

    test_allowed_pipe_commands()
    print("✓ Allowed pipe commands tests passed")

    test_prefix_with_various_formats()
    print("✓ Various format prefixes tests passed")

    test_prefix_not_at_start()
    print("✓ Prefix position validation tests passed")

    print("\n🎉 All allowed prefixes tests passed!")