"""Agent setup and management for network automation."""

import time
import uuid
from collections import deque
from datetime import datetime
from typing import Annotated, Any, Dict, Optional

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.errors import GraphRecursionError
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from typing_extensions import TypedDict

from .network_device import DeviceConnection

# Model fallback chain - order matters (primary to fallback)
MODEL_FALLBACK_CHAIN = [
    "openai/gpt-oss-120b",  # Primary (best for networking)
    "llama-3.3-70b-versatile",  # Fallback 1 (high quality)
    "llama-3.1-8b-instant",  # Fallback 2 (fast & economical)
]


class AgentState(TypedDict):
    """Type-safe agent state schema."""

    messages: Annotated[list[BaseMessage], add_messages]


class Agent:
    """AI-powered agent for network automation with advanced features."""

    def __init__(
        self,
        groq_api_key: str,
        device: DeviceConnection,
        model_name: str = "openai/gpt-oss-120b",
        temperature: float = 0.1,
        verbose: bool = False,
        timeout: int = 60,
    ) -> None:
        """Initialize the agent.

        Args:
            groq_api_key: Groq API key
            device: DeviceConnection instance
            model_name: Model to use (openai/gpt-oss-120b, llama-3.3-70b-versatile, etc.)
            temperature: Response randomness (0.0-1.0)
            verbose: Enable detailed logging
            timeout: API request timeout in seconds
        """
        self.device = device
        self.verbose = verbose
        self.timeout = timeout
        self.command_history = []
        self.groq_api_key = groq_api_key

        # Rate limiting
        self.rate_limit_requests = 30
        self.rate_limit_window = 60
        self.request_times = deque()

        # Model fallback tracking
        self.primary_model = model_name
        self.current_model = model_name
        self.temperature = temperature
        self.model_fallback_count = 0
        self.model_usage_stats: dict[str, int] = {}

        # Initialize LLM with primary model
        self.llm = self._initialize_llm(model_name, temperature, timeout)

        # Create a tool the AI can use to run commands
        self.execute_command_tool = tool("execute_show_command")(
            self._execute_device_command
        )

        # Create the AI agent with the tool
        self.agent = create_react_agent(self.llm, [self.execute_command_tool])

        if self.verbose:
            print(f"✓ Agent initialized (Model: {model_name}, Temp: {temperature})")

    def _initialize_llm(
        self, model_name: str, temperature: float, timeout: int
    ) -> ChatGroq:
        """Initialize ChatGroq LLM with specified model."""
        return ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name=model_name,
            temperature=temperature,
            request_timeout=timeout,
        )

    def _get_next_fallback_model(self) -> str | None:
        """Get next fallback model in chain."""
        try:
            current_index = MODEL_FALLBACK_CHAIN.index(self.current_model)
            if current_index + 1 < len(MODEL_FALLBACK_CHAIN):
                next_model = MODEL_FALLBACK_CHAIN[current_index + 1]
                return next_model
        except ValueError:
            pass
        return None

    def _switch_to_fallback_model(self) -> bool:
        """Switch to next fallback model if available.

        Returns:
            True if successfully switched, False if no more fallbacks
        """
        next_model = self._get_next_fallback_model()
        if not next_model:
            return False

        try:
            old_model = self.current_model
            self.current_model = next_model
            self.model_fallback_count += 1
            self.llm = self._initialize_llm(next_model, self.temperature, self.timeout)
            self.agent = create_react_agent(self.llm, [self.execute_command_tool])

            if self.verbose:
                print(
                    f"⚠️  Switched from {old_model} → {next_model} (fallback #{self.model_fallback_count})"
                )

            return True
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to switch model: {e}")
            return False

    def _execute_device_command(self, command: str) -> str:
        """Execute a command on the device (used by AI)."""
        timestamp = datetime.now().isoformat()
        try:
            if self.verbose:
                print(f"[{timestamp}] Executing: {command}")

            output = self.device.execute_command(command)

            # Log to history
            self.command_history.append({
                'timestamp': timestamp,
                'command': command,
                'output_length': len(output),
                'success': True,
            })

            return output
        except Exception as e:
            self.command_history.append({
                'timestamp': timestamp,
                'command': command,
                'error': str(e),
                'success': False,
            })
            return f"Error executing command: {str(e)}"

    def _check_rate_limit(self) -> bool:
        """Check if rate limit has been exceeded."""
        current_time = time.time()

        # Remove old requests outside time window
        while (
            self.request_times
            and current_time - self.request_times[0] > self.rate_limit_window
        ):
            self.request_times.popleft()

        # Check limit
        if len(self.request_times) >= self.rate_limit_requests:
            return False

        self.request_times.append(current_time)
        return True

    def answer_question(self, question: str, context: str | None = None) -> str:
        """Answer a question about the device with model fallback on rate limit.

        Args:
            question: User's question
            context: Optional context for the AI

        Returns:
            Response from the AI or error message
        """
        # Check rate limit
        if not self._check_rate_limit():
            wait_time = self.rate_limit_window - (time.time() - self.request_times[0])
            return f"⚠ Rate limit exceeded. Please wait {int(wait_time)}s."

        # Enhanced system prompt
        system_prompt = """You are an expert network engineer assistant specializing in Cisco devices.

CRITICAL RULES:
1. ALWAYS use the execute_show_command tool to run commands
2. DO NOT make assumptions about command output
3. Run commands and analyze their actual output
4. If a command fails, try an alternative command

Guidelines:
- Use execute_show_command tool to run Cisco CLI commands
- Run multiple commands if needed to fully answer the question
- Provide clear, concise explanations
- Format output in a readable way
- Highlight important findings (errors, warnings, issues)

Common command patterns:
- VLANs: show vlan brief, show vlan
- Interfaces: show ip interface brief, show interfaces status
- Routing: show ip route, show ip protocols
- Version: show version
- Config: show running-config (specific sections)
- Logs: show logging
- Neighbors: show cdp neighbors, show lldp neighbors

IMPORTANT: You MUST execute commands to answer questions. Don't provide theoretical answers."""

        if context:
            system_prompt += f"\n\nAdditional context: {context}"

        # Combine system prompt with user query
        full_query = f"{system_prompt}\n\nUser question: {question}"

        max_retries = len(MODEL_FALLBACK_CHAIN)
        retry_count = 0

        while retry_count < max_retries:
            try:
                start_time = time.time()

                if self.verbose and retry_count > 0:
                    print(f"\n🔄 Retry #{retry_count} with {self.current_model}...")

                result = self.agent.invoke(
                    {"messages": [("user", full_query)]},
                    config={
                        "recursion_limit": 8,  # Max 8 tool calls
                        "configurable": {"thread_id": str(uuid.uuid4())},
                    },
                )

                elapsed_time = time.time() - start_time

                # Track model usage
                if self.current_model not in self.model_usage_stats:
                    self.model_usage_stats[self.current_model] = 0
                self.model_usage_stats[self.current_model] += 1

                # Extract the AI's response (find last AI message, skip tool messages)
                if isinstance(result, dict) and "messages" in result:
                    messages = result["messages"]
                    response = None
                    for msg in reversed(messages):
                        if isinstance(msg, AIMessage):
                            response = msg.content
                            break
                    if response is None:
                        response = str(messages[-1]) if messages else "No response"
                else:
                    response = str(result)

                if self.verbose:
                    print(
                        f"✓ Query completed in {elapsed_time:.2f}s (Model: {self.current_model})"
                    )

                return response

            except GraphRecursionError:
                return "⚠ Agent exceeded maximum iterations (too many tool calls). Try a simpler query."

            except TimeoutError:
                error_msg = f"⚠ Request timeout with {self.current_model}"
                if self._switch_to_fallback_model():
                    print(f"{error_msg}, trying fallback model...")
                    retry_count += 1
                    time.sleep(1)  # Brief delay before retry
                    continue
                return error_msg

            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = (
                    "rate limit" in error_str
                    or "rate_limit" in error_str
                    or "429" in error_str
                    or "quota" in error_str
                )

                if is_rate_limit:
                    error_msg = f"⚠ Rate limit hit on {self.current_model}"
                    if self._switch_to_fallback_model():
                        print(f"{error_msg}, switching to {self.current_model}...")
                        retry_count += 1
                        time.sleep(2)  # Longer delay for rate limits
                        continue
                    return f"{error_msg}. No more fallback models available."

                # Non-rate-limit error
                return f"❌ Error: {str(e)}"

    def execute_direct_command(self, command: str) -> str:
        """Execute a command directly without AI processing.

        Useful for debugging or when AI is slow/unavailable.
        """
        try:
            if self.verbose:
                print(f"⚡ Executing: {command}")

            output = self.device.execute_command(command)

            # Log to history
            self.command_history.append({
                'timestamp': datetime.now().isoformat(),
                'command': command,
                'output_length': len(output),
                'success': True,
                'direct': True,
            })

            return output
        except Exception as e:
            return f"Error: {str(e)}"

    def get_statistics(self) -> dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary with command statistics, rate limit status, and model info
        """
        successful = sum(1 for cmd in self.command_history if cmd.get('success', False))
        failed = len(self.command_history) - successful
        rate_limit_active = len(self.request_times) >= self.rate_limit_requests

        return {
            'total_commands': len(self.command_history),
            'successful_commands': successful,
            'failed_commands': failed,
            'rate_limit_used': f"{len(self.request_times)}/{self.rate_limit_requests}",
            'rate_limit_active': rate_limit_active,
            'primary_model': self.primary_model,
            'current_model': self.current_model,
            'model_fallbacks': self.model_fallback_count,
            'model_usage': self.model_usage_stats,
        }

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get command history.

        Args:
            limit: Number of recent commands to return

        Returns:
            List of command history entries
        """
        return self.command_history[-limit:] if self.command_history else []
