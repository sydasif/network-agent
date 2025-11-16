"""Enhanced agent with device context understanding."""

import logging
import re
from typing import Annotated, Optional, Tuple

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.errors import GraphRecursionError
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .audit import AuditLogger
from .exceptions import CommandBlockedError
from .logging_config import get_verbose_logger
from .security import CommandSecurityPolicy
from .sensitive_data import SensitiveDataProtector


logger = logging.getLogger("net_agent.agent")
verbose_logger = get_verbose_logger()


class AgentState(TypedDict):
    """Type-safe agent state schema."""

    messages: Annotated[list[BaseMessage], add_messages]


class EnhancedAgent:
    """AI-powered agent with device context understanding."""

    def __init__(
        self,
        groq_api_key: str,
        device_manager,  # DeviceManager instance
        inventory_manager,  # InventoryManager instance
        model_name: str,
        temperature: float = 0.1,
        verbose: bool | None = None,
        timeout: int = 60,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        """Initialize the enhanced agent."""
        self.device_manager = device_manager
        self.inventory_manager = inventory_manager
        self.verbose = verbose
        self.timeout = timeout
        self.groq_api_key = groq_api_key
        self.data_protector = SensitiveDataProtector()
        self.model_name = model_name
        self.temperature = temperature
        self.audit_logger = audit_logger
        self.security_policy = CommandSecurityPolicy()
        self.llm = self._initialize_llm(model_name, temperature, timeout)

        if verbose is None:
            from .settings import settings

            self.verbose = settings.verbose

        if self.verbose:
            verbose_logger.setLevel(logging.DEBUG)
        else:
            verbose_logger.setLevel(logging.INFO)

        # Import for ReAct agent
        from langchain_core.prompts import PromptTemplate
        from langchain.agents import create_react_agent

        self.execute_command_tool = tool("execute_show_command")(
            self._execute_device_command
        )

        # Define tools list
        tools = [self.execute_command_tool]

        # Template for ReAct agent format
        template = """You act as a network engineer assistant. You always run real device commands with `execute_show_command`.

Your replies stay short and clear. You focus on real output, highlight issues, and run extra commands when needed.
You work with common tasks such as VLANs, interfaces, routing, logs, version checks, configs, and neighbor discovery.

After executing all necessary commands, provide a clear summary of the results to answer the user's question.

Do not end your response with 'need more steps' or similar phrases unless you actually need more information from the user.

Format your responses in a structured way for network data:
- Use bullet points for lists of items (interfaces, neighbors, etc.)
- Use clear headings when appropriate (## OSPF Configuration, ## Interface Status, etc.)
- Highlight important values with bold (e.g., **Process ID: 1**)
- For tables of data, use markdown table format
- Organize information by category (Configuration, Status, Issues, etc.)

Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent_runnable = create_react_agent(
            self.llm, tools, prompt
        )
        self.agent = AgentExecutor(
            agent=agent_runnable,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=self.verbose,
        )

        logger.info("Enhanced agent initialized with ReAct agent format")

    def _initialize_llm(
        self, model_name: str, temperature: float, timeout: int
    ) -> ChatGroq:
        """Initialize ChatGroq LLM."""
        return ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name=model_name,
            temperature=temperature,
            request_timeout=timeout,
        )

    def _extract_device_reference(self, question: str) -> Tuple[Optional[str], str]:
        """Extract device name from natural language question.

        Examples:
        - "show me vlans on SW1" -> ("SW1", "show me vlans")
        - "what's the uptime on RTR1" -> ("RTR1", "what's the uptime")
        - "get ip route from EDGE-RTR-1" -> ("EDGE-RTR-1", "get ip route")
        - "show version" -> (None, "show version")

        Returns:
            Tuple of (device_name, cleaned_question)
        """
        # Pattern to match device references
        patterns = [
            r"\bon\s+([A-Z0-9_-]+)",  # "on SW1", "on RTR1"
            r"\bfrom\s+([A-Z0-9_-]+)",  # "from SW1", "from RTR1"
            r"\bat\s+([A-Z0-9_-]+)",  # "at SW1", "at RTR1"
            r"\bfor\s+([A-Z0-9_-]+)",  # "for SW1", "for RTR1"
            r"\bof\s+([A-Z0-9_-]+)",  # "of SW1", "of RTR1"
            r"^([A-Z0-9_-]+)\s+",  # "SW1 show vlans" (device at start)
        ]

        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                device_name = match.group(1).upper()

                # Check if this device exists in inventory
                if self.inventory_manager and device_name in self.inventory_manager:
                    # Remove the device reference from question
                    cleaned_question = re.sub(
                        pattern, " ", question, flags=re.IGNORECASE
                    ).strip()

                    # Clean up extra spaces
                    cleaned_question = " ".join(cleaned_question.split())

                    verbose_logger.debug(
                        f"Extracted device: {device_name}, "
                        f"cleaned question: {cleaned_question}"
                    )

                    return device_name, cleaned_question

        return None, question

    def _switch_to_device(self, device_name: str) -> bool:
        """Switch to a device by name from inventory.

        Args:
            device_name: Name of device in inventory

        Returns:
            True if switched successfully
        """
        # Get device from inventory
        device_info = self.inventory_manager.get_device(device_name)

        if not device_info:
            logger.warning(f"Device '{device_name}' not found in inventory")
            return False

        # Check if device is already connected
        if self.device_manager.is_connected(device_name):
            # Just switch to it
            try:
                self.device_manager.switch_device(device_name)
                verbose_logger.info(f"Switched to existing device '{device_name}'")
                return True
            except ValueError as e:
                logger.warning(f"Could not switch to '{device_name}': {e}")
                return False

        # Device not connected, connect to it
        try:
            verbose_logger.info(
                f"Connecting to '{device_name}' ({device_info.hostname})..."
            )
            success = self.device_manager.connect_to_device(device_name, device_info)
            if success:
                verbose_logger.info(f"✓ Connected to {device_name}")
            else:
                logger.error(f"Failed to connect to {device_name}")
            return success
        except Exception as e:
            logger.error(f"Error connecting to {device_name}: {e}")
            return False

    def _execute_device_command(self, command: str) -> str:
        """Execute a command after validation and device selection."""
        # Get current connection
        current_connection = self.device_manager.get_current_connection()
        if not current_connection:
            return "❌ No device connected. Please connect to a device first."

        # Validate command
        try:
            self.security_policy.validate_command(command)
        except CommandBlockedError as e:
            if self.audit_logger:
                self.audit_logger.log_command_blocked(command, e.reason)
            return f"⚠ BLOCKED: {e.reason}"

        return self._execute_validated_command(command, current_connection)

    def _execute_validated_command(self, command: str, device_connection) -> str:
        """Execute a validated command on the specified device."""
        try:
            verbose_logger.debug("Executing: %s", command)
            output = device_connection.execute_command(command)
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command, success=True, output_length=len(output)
                )
            return output
        except ConnectionError as e:
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command, success=False, error=str(e)
                )
            return f"❌ Connection Error: {e}"
        except Exception as e:
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command, success=False, error=str(e)
                )
            return f"⚠️ Error: {e}"

    def answer_question(self, question: str) -> str:
        """Answer a question, handling device selection automatically."""
        # Extract device reference from question
        device_name, cleaned_question = self._extract_device_reference(question)

        if device_name:
            # Try to switch to the specified device
            if not self._switch_to_device(device_name):
                return f"❌ Could not switch to device '{device_name}'. Check if it exists in inventory."
        else:
            # No device specified, use current device or fail
            current_device = self.device_manager.get_current_device_name()
            if not current_device:
                return "❌ No device specified and no current device connected. Please specify a device from your inventory."

        # Process the question with the LLM
        try:
            verbose_logger.info("Processing Query: %s", cleaned_question)
            result = self.agent.invoke(
                {"input": cleaned_question}, config={"recursion_limit": 8}
            )
            response = self._extract_response(result)
            verbose_logger.info("Query completed.")
            return response
        except GraphRecursionError:
            return "⚠ Agent exceeded maximum iterations. Try a simpler query."
        except TimeoutError:
            return f"⚠ Request timeout with {self.model_name}"
        except Exception as e:
            return self._handle_error(e)

    def _extract_response(self, result) -> str:
        """Extract the AI response."""
        if isinstance(result, dict) and "output" in result:
            return result["output"]
        return "Sorry, I encountered an issue."

    def _handle_error(self, e: Exception) -> str:
        """Handle exceptions during query processing."""
        error_str = str(e).lower()
        if "rate limit" in error_str or "429" in error_str:
            return f"⚠ Rate limit hit on {self.model_name}. Please wait."
        sanitized_error = self.data_protector.sanitize_error(str(e))
        return f"❌ Error: {sanitized_error}"
