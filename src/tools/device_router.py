"""LangChain tool for device routing and management."""

import logging
from typing import Tuple
from langchain_core.tools import tool

from ..device_router import DeviceRouter


logger = logging.getLogger("net_agent.tools.device_router")


class DeviceRouterTool:
    """Class to create LangChain tool for device routing."""
    
    def __init__(self, device_router: DeviceRouter):
        self.device_router = device_router

    def create_extract_device_tool(self):
        """Create the extract_device tool."""
        
        @tool
        def extract_device(question: str) -> dict:
            """
            Extract device name from natural language question and return cleaned question.
            
            Args:
                question: Natural language question that may contain device reference
                
            Returns:
                dict: Contains 'device_name' and 'cleaned_question' keys
            """
            device_name, cleaned_question = self.device_router.extract_device_reference(question)
            return {
                "device_name": device_name,
                "cleaned_question": cleaned_question
            }

        return extract_device

    def create_route_to_device_tool(self):
        """Create the route_to_device tool."""
        
        @tool
        def route_to_device(device_name: str) -> str:
            """
            Route to a device by name from inventory.
            
            Args:
                device_name: Name of device in inventory
                
            Returns:
                str: Routing status message
            """
            success = self.device_router.route_to_device(device_name)
            if success:
                return f"Successfully routed to device: {device_name}"
            else:
                return f"Failed to route to device: {device_name}"

        return route_to_device