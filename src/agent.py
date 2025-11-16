"""Agent setup and management for network automation."""

import logging
from typing import Annotated

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
from .network_device import DeviceConnection
from .security import CommandSecurityPolicy
from .sensitive_data import SensitiveDataProtector


logger = logging.getLogger("net_agent.agent")
verbose_logger = get_verbose_logger()


class AgentState(TypedDict):
    """Type-safe agent state schema."""

    messages: Annotated[list[BaseMessage], add_messages]


class Agent:
    """AI-powered agent for network automation."""

    def __init__(
        self,
        groq_api_key: str,
        device: DeviceConnection,
        model_name: str,
        temperature: float = 0.1,
        verbose: bool | None = None,  # ✅ Allow None to use settings
        timeout: int = 60,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        """Initialize the agent."""
        self.device = device
        # Use settings.verbose as default if not explicitly provided
        if verbose is None:
            from .settings import settings

            verbose = settings.verbose
        self.verbose = verbose
        self.timeout = timeout
        self.groq_api_key = groq_api_key
        self.data_protector = SensitiveDataProtector()
        self.model_name = model_name
        self.temperature = temperature
        self.audit_logger = audit_logger
        self.security_policy = CommandSecurityPolicy()
        self.llm = self._initialize_llm(model_name, temperature, timeout)

        if self.verbose:
            verbose_logger.setLevel(logging.DEBUG)
        else:
            verbose_logger.setLevel(logging.INFO)

        from langchain_core.prompts import ChatPromptTemplate

        from .prompts import SYSTEM_PROMPT

        self.execute_command_tool = tool("execute_show_command")(
            self._execute_device_command
        )
        tools = [self.execute_command_tool]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        agent_runnable = create_tool_calling_agent(self.llm, tools, prompt)
        self.agent = AgentExecutor(
            agent=agent_runnable,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=self.verbose,
        )

        logger.info("Agent initialized with model: %s", model_name)

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

    def _execute_device_command(self, command: str) -> str:
        """Execute a command after validation."""
        try:
            self.security_policy.validate_command(command)
        except CommandBlockedError as e:
            if self.audit_logger:
                self.audit_logger.log_command_blocked(command, e.reason)
            return f"⚠ BLOCKED: {e.reason}"
        return self._execute_validated_command(command)

    def _execute_validated_command(self, command: str) -> str:
        """Execute a validated command."""
        try:
            verbose_logger.debug("Executing: %s", command)
            output = self.device.execute_command(command)
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
        """Answer a question about the device."""
        try:
            verbose_logger.info("Processing Query...")
            result = self.agent.invoke(
                {"input": question}, config={"recursion_limit": 8}
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
