"""Pydantic models for structured data contracts across the application.

This module defines the data models used throughout the application to ensure
consistent data contracts between components. The models are organized into
tooling models and NLP pre-processing models.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# --- Tooling Models ---


class DeviceInfo(BaseModel):
    """Data model for a single network device.

    Attributes:
        name (str): The unique name identifier for the device.
        hostname (str): The IP address or hostname for connecting to the device.
        role (Optional[str]): The role of the device in the network (e.g., 'access', 'distribution').
        device_type (str): The Netmiko device type (e.g., 'cisco_ios', 'cisco_xr').
    """

    name: str = Field(..., description="The name of the device.")
    hostname: str = Field(..., description="The IP address or hostname.")
    role: Optional[str] = Field(
        None, description="The role of the device in the network."
    )
    device_type: str = Field(
        ..., description="The Netmiko device type (e.g., cisco_ios)."
    )


class CommandOutput(BaseModel):
    """Structured output for a network command.

    Attributes:
        device_name (str): The name of the device the command was run on.
        command (str): The command that was executed.
        output (str): The raw, sanitized output from the device.
        status (str): Status of the command execution ('success' or 'error').
        error_message (Optional[str]): Details if an error occurred during execution.
    """

    device_name: str = Field(..., description="The device the command was run on.")
    command: str = Field(..., description="The command that was executed.")
    output: str = Field(..., description="The raw, sanitized output from the device.")
    status: str = Field("success", description="Either 'success' or 'error'.")
    error_message: Optional[str] = Field(
        None, description="Details if an error occurred."
    )


# --- NLP Models ---

class ExtractedEntities(BaseModel):
    """Entities extracted from the user's network query."""
    device_names: List[str] = Field(default_factory=list, description="List of device hostnames mentioned (e.g., 'S1', 'R1').")
    interfaces: List[str] = Field(default_factory=list, description="List of interface names (e.g., 'GigabitEthernet0/1').")
    protocols: List[str] = Field(default_factory=list, description="List of protocols (e.g., 'bgp', 'ospf').")
    ip_addresses: List[str] = Field(default_factory=list, description="List of IP addresses found.")
    vlans: List[str] = Field(default_factory=list, description="List of VLAN IDs found.")

class UserIntent(BaseModel):
    """
    Analyze the user's network query and extract structured information.
    """
    intent: Literal["get_status", "get_config", "find_device", "greeting", "unknown"] = Field(
        ..., description="The primary goal of the user."
    )
    entities: ExtractedEntities = Field(
        ..., description="All named entities recognized in the query."
    )
    is_ambiguous: bool = Field(
        False, description="True if the user asks for status/config but specifies no device."
    )
    sentiment: Literal["normal", "urgent"] = Field(
        "normal", description="Urgent if words like 'down', 'critical', or 'emergency' are used."
    )
