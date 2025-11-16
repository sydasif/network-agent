"""Agent setup and management for network automation."""

import sys
from typing import Annotated

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.errors import GraphRecursionError
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .audit import AuditLogger
from .network_device import DeviceConnection
from .security import CommandSecurityPolicy
from .sensitive_data import SensitiveDataProtector


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    @staticmethod
    def disable():
        """Disable colors for non-terminal environments."""
        for attr in dir(Colors):
            if attr.isupper():
                setattr(Colors, attr, "")


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
        verbose: bool = False,
        timeout: int = 60,
        audit_logger: AuditLogger = None,
    ) -> None:
        """Initialize the agent."""
        self.device = device
        self.verbose = verbose
        self.timeout = timeout
        self.groq_api_key = groq_api_key
        self.data_protector = SensitiveDataProtector()
        self.model_name = model_name
        self.temperature = temperature
        self.audit_logger = audit_logger
        self.security_policy = CommandSecurityPolicy()
        self.llm = self._initialize_llm(model_name, temperature, timeout)

        if not sys.stdout.isatty():
            Colors.disable()

        from langchain_core.prompts import ChatPromptTemplate

        self.execute_command_tool = tool("execute_show_command")(
            self._execute_device_command
        )
        tools = [self.execute_command_tool]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a network engineer assistant..."),
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

        if self.verbose:
            print(f"✓ Agent initialized (Model: {model_name})")

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
        is_valid, reason = self.security_policy.validate_command(command)
        if not is_valid:
            if self.audit_logger:
                self.audit_logger.log_command_blocked(command, reason)
            return f"⚠ BLOCKED: {reason}"
        return self._execute_validated_command(command)

    def _execute_validated_command(self, command: str) -> str:
        """Execute a validated command."""
        try:
            if self.verbose:
                print(f"{Colors.GRAY}Executing:{Colors.RESET} {command}")
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
            if self.verbose:
                print(f"\n{Colors.CYAN}Processing Query...{Colors.RESET}")
            result = self.agent.invoke(
                {"input": question}, config={"recursion_limit": 8}
            )
            response = self._extract_response(result)
            if self.verbose:
                print(f"\n{Colors.GREEN}✓ Query completed.{Colors.RESET}")
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
