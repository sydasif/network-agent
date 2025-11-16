"""Simple LLM agent for network automation."""

import logging
from typing import Annotated, Optional

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
from .sensitive_data import SensitiveDataProtector


logger = logging.getLogger("net_agent.simple_agent")
verbose_logger = get_verbose_logger()


class AgentState(TypedDict):
    """Type-safe agent state schema."""

    messages: Annotated[list[BaseMessage], add_messages]


class SimpleAgent:
    """Simple AI-powered agent for network automation."""

    def __init__(
        self,
        groq_api_key: str,
        model_name: str,
        temperature: float = 0.1,
        verbose: bool | None = None,
        timeout: int = 60,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        """Initialize the simple agent."""
        self.verbose = verbose
        self.timeout = timeout
        self.groq_api_key = groq_api_key
        self.data_protector = SensitiveDataProtector()
        self.model_name = model_name
        self.temperature = temperature
        self.audit_logger = audit_logger
        self.llm = self._initialize_llm(model_name, temperature, timeout)

        if verbose is None:
            from .settings import settings

            self.verbose = settings.verbose

        if self.verbose:
            verbose_logger.setLevel(logging.DEBUG)
        else:
            verbose_logger.setLevel(logging.INFO)

        # Create a placeholder for the execute command tool that will be set later
        # This is a temporary solution since we need the tool to reference session management
        self.execute_command_tool = None

        # For now, we'll create a basic agent without the execute_command_tool
        from langchain_core.prompts import PromptTemplate
        from langchain.agents import create_react_agent

        # Define tools list (empty for now)
        tools = []

        # Template for ReAct agent format
        template = """You are a network engineer assistant. 

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

        logger.info("Simple agent initialized")

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

    def answer_question(self, question: str) -> str:
        """Answer a question using the LLM."""
        # Process the question with the LLM
        try:
            verbose_logger.info("Processing Query: %s", question)
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