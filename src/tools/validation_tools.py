"""LangChain tools for validation and sanitization."""

import logging
from langchain_core.tools import tool

from ..validation import ValidationPipeline
from ..sensitive_data import SensitiveDataProtector


logger = logging.getLogger("net_agent.tools.validation_tools")


class ValidationTools:
    """Class to create LangChain tools for validation and sanitization."""
    
    def __init__(self, validation_pipeline: ValidationPipeline):
        self.validation_pipeline = validation_pipeline
        self.data_protector = SensitiveDataProtector()

    def create_validate_query_tool(self):
        """Create the validate_query tool."""
        
        @tool
        def validate_query(query: str) -> str:
            """
            Validate a user query before processing.
            
            Args:
                query: User input query to validate
                
            Returns:
                str: Validation result message
            """
            try:
                self.validation_pipeline.validate_query(query)
                return "Query is valid and safe to process."
            except Exception as e:
                return f"Query validation failed: {str(e)}"

        return validate_query

    def create_sanitize_query_tool(self):
        """Create the sanitize_query tool."""
        
        @tool
        def sanitize_query(query: str) -> str:
            """
            Sanitize query by removing/escaping dangerous content.
            
            Args:
                query: Raw user input query to sanitize
                
            Returns:
                str: Sanitized query safe for processing
            """
            sanitized = self.validation_pipeline.sanitize_query(query)
            return sanitized

        return sanitize_query

    def create_validate_command_tool(self):
        """Create the validate_command tool."""
        
        @tool
        def validate_command(command: str) -> str:
            """
            Validate a command using security policy rules.
            
            Args:
                command: The command to validate
                
            Returns:
                str: Validation result message
            """
            try:
                self.validation_pipeline.validate_command(command)
                return "Command is valid and safe to execute."
            except Exception as e:
                return f"Command validation failed: {str(e)}"

        return validate_command