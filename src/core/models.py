"""Simplified Pydantic models for the network agent.

This module defines the minimal data models needed for the simplified application.
"""

from typing import Optional

from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    """Data model for a single network device.

    Attributes:
        name: The name of the device
        hostname: The IP address or hostname of the device
        platform: The device platform (e.g., cisco_ios)
        role: The role of the device in the network (optional)
    """

    name: str = Field(..., description="The name of the device.")
    hostname: str = Field(..., description="The IP address or hostname.")
    platform: str = Field(..., description="The device platform (e.g., cisco_ios).")
    role: Optional[str] = Field(
        None, description="The role of the device in the network."
    )


class CommandOutput(BaseModel):
    """Output for a network command.

    Attributes:
        device_name: The device the command was run on
        command: The command that was executed
        output: The output from the device
        status: Either 'success' or 'error'
        error_message: Details if an error occurred (optional)
    """

    device_name: str = Field(..., description="The device the command was run on.")
    command: str = Field(..., description="The command that was executed.")
    output: str = Field(..., description="The output from the device.")
    status: str = Field("success", description="Either 'success' or 'error'.")
    error_message: Optional[str] = Field(
        None, description="Details if an error occurred."
    )


class CommandRequest(BaseModel):
    """Request model for executing a network command.

    Attributes:
        device_name: The device to execute command on
        command: The command to execute
    """

    device_name: str = Field(..., description="The device to execute command on.")
    command: str = Field(..., description="The command to execute.")
