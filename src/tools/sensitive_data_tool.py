"""LangChain tool for sensitive data sanitization."""

import logging
from langchain_core.tools import tool

from ..sensitive_data import SensitiveDataProtector


logger = logging.getLogger("net_agent.tools.sensitive_data_tool")


class SensitiveDataTool:
    """Class to create LangChain tool for sensitive data sanitization."""
    
    def __init__(self):
        self.data_protector = SensitiveDataProtector()

    def create_sanitize_output_tool(self):
        """Create the sanitize_output tool."""
        
        @tool
        def sanitize_output(text: str) -> str:
            """
            Sanitize text to remove sensitive data before logging or displaying.
            
            Args:
                text: Text to sanitize
                
            Returns:
                str: Sanitized text with sensitive data redacted
            """
            sanitized = self.data_protector.sanitize_for_logging(text)
            return sanitized

        return sanitize_output