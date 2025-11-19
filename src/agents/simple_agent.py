"""Simplified LangChain-based AI agent for network command execution.

This module implements a simple AI agent that interprets natural language requests
and executes appropriate network commands using Nornir.
"""

from typing import Dict

from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_groq import ChatGroq

from src.core.config import settings
from src.core.network_manager import NetworkManager


class NetworkCommand(BaseModel):
    """Model for extracted network command information.

    Attributes:
        device_name: The name of the device where the command should be executed
        command: The network command to be executed on the device
    """

    device_name: str = Field(..., description="The device to execute the command on")
    command: str = Field(..., description="The network command to execute")


class SimpleNetworkAgent:
    """A simplified AI agent for network command execution.

    This agent takes natural language input, determines the appropriate network
    command to execute, and uses Nornir to execute it on the specified device.

    Attributes:
        llm: The LLM instance used for processing natural language requests
        network_manager: Instance of NetworkManager for executing commands on devices
        prompt_template: Template for formatting requests to the LLM
        extractor: LLM with structured output for extracting device and command
    """

    def __init__(self, api_key: str):
        """Initialize the agent with an LLM instance.

        Args:
            api_key: The API key for the Groq LLM service
        """
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=settings.groq_model_name,
            temperature=settings.groq_temperature,
        )
        self.network_manager = NetworkManager()

        self.prompt_template = PromptTemplate.from_template(
            """You are a network assistant. Extract the device name and network command from the user's request.

User request: {user_input}

Provide the device name and the network command to execute in JSON format.
If the user doesn't specify a particular device, choose one from the network: {available_devices}

Respond with a JSON object like this:
{{
    "device_name": "device_name",
    "command": "the network command to execute"
}}

Network commands should be standard CLI commands like 'show version', 'show interfaces', etc."""
        )

        self.extractor = self.prompt_template | self.llm.with_structured_output(
            NetworkCommand
        )

    def process_request(self, user_input: str) -> Dict[str, str]:
        """Process a natural language request and execute the appropriate command.

        Args:
            user_input: Natural language request from the user

        Returns:
            Dictionary with device name, command, and output
        """
        # Get list of available network devices
        available_devices = self.network_manager.get_device_names()

        # Use LLM to extract device name and command from user input
        result: NetworkCommand = self.extractor.invoke(
            {"user_input": user_input, "available_devices": available_devices}
        )

        # Execute the extracted command on the specified device
        output = self.network_manager.execute_command(
            result.device_name, result.command
        )

        # Return structured response containing device, command, and output
        return {
            "device_name": result.device_name,
            "command": result.command,
            "output": output,
        }

    def close_sessions(self):
        """Close all network sessions."""
        self.network_manager.close_all_sessions()
