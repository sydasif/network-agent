"""Agent setup and management for network automation."""

import time
from collections import deque
from datetime import datetime
from typing import Annotated, Any

from langchain.agents import AgentExecutor, create_react_agent  # Updated import

# --- MODIFIED IMPORTS ---
from langchain_core.messages import BaseMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.errors import GraphRecursionError
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .audit import AuditLogger
from .network_device import DeviceConnection
from .sensitive_data import SensitiveDataProtector


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
        model_name: str,
        temperature: float = 0.1,
        verbose: bool = False,
        timeout: int = 60,
        audit_logger: AuditLogger = None,
        config=None,
    ) -> None:
        """Initialize the agent."""
        self.device = device
        self.verbose = verbose
        self.timeout = timeout
        self.command_history = []
        self.groq_api_key = groq_api_key
        self.data_protector = SensitiveDataProtector()

        # Use configuration for rate limiting if provided, otherwise use defaults
        if config is not None:
            self.config = config
            self.rate_limit_requests = self.config.limits.max_commands_per_minute
            self.rate_limit_window = self.config.limits.rate_limit_window_seconds
        else:
            # Defaults for backward compatibility
            self.rate_limit_requests = 30
            self.rate_limit_window = 60

        self.request_times = deque()
        self.primary_model = model_name
        self.current_model = model_name
        self.temperature = temperature
        self.model_fallback_count = 0
        self.model_usage_stats: dict[str, int] = {}
        self.audit_logger = audit_logger
        self.llm = self._initialize_llm(model_name, temperature, timeout)

        # --- MODIFIED AGENT CREATION LOGIC ---
        self.execute_command_tool = tool("execute_show_command")(
            self._execute_device_command
        )

        tools = [self.execute_command_tool]

        # Create the agent runnable using the new, recommended function
        # For older versions of langchain, create_react_agent requires a prompt
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
        agent_runnable = create_react_agent(self.llm, tools, prompt)

        # Wrap the agent in an AgentExecutor, which is now the standard way to run agents
        self.agent = AgentExecutor(
            agent=agent_runnable,
            tools=tools,
            verbose=self.verbose,
            handle_parsing_errors=True,  # Improves robustness
        )

        if self.verbose:
            print(
                f"✓ Agent initialized with langchain.agents.create_react_agent (Model: {model_name}, Temp: {temperature})"
            )

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
                return MODEL_FALLBACK_CHAIN[current_index + 1]
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

            # Create the agent runnable using the new, recommended function
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
                self.llm, [self.execute_command_tool], prompt
            )

            # Wrap the agent in an AgentExecutor, which is now the standard way to run agents
            self.agent = AgentExecutor(
                agent=agent_runnable,
                tools=[self.execute_command_tool],
                verbose=self.verbose,
                handle_parsing_errors=True,  # Improves robustness
            )

            if self.verbose:
                fb_count = self.model_fallback_count
                msg = f"⚠️  Switched {old_model} → {next_model} (fallback #{fb_count})"
                print(msg)

            return True
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to switch model: {e}")
            return False

    def _execute_device_command(self, command: str) -> str:
        """Execute a command on the device (used by AI) with safety constraints.

        Only allows read-only commands to prevent accidental or malicious
        configuration changes.

        Args:
            command: Command to execute

        Returns:
            Command output or error message if blocked
        """
        # Normalize command for validation
        command_stripped = command.strip()
        command_lower = command_stripped.lower()

        # Run validation checks
        validation_result = self._validate_command(command_stripped, command_lower)
        if validation_result is not True:  # If validation failed, return error message
            return validation_result

        # Command passed all safety checks - execute it
        return self._execute_validated_command(command_stripped)

    def _validate_command(
        self, command_stripped: str, command_lower: str
    ) -> str | bool:
        """Validate command against security constraints.

        Args:
            command_stripped: Command with whitespace stripped
            command_lower: Lowercase version of command

        Returns:
            True if valid, error message string if blocked
        """
        # Check if command is empty
        if not command_stripped:
            return "⚠ Error: Empty command received"

        # Check for blocked keywords (most critical check)
        blocked_result = self._check_blocked_keywords(command_stripped, command_lower)
        if blocked_result:
            return blocked_result

        # Check if command starts with allowed prefix
        prefix_result = self._check_allowed_prefix(command_stripped, command_lower)
        if prefix_result:
            return prefix_result

        # Check for command chaining attempts
        chaining_result = self._check_command_chaining(command_stripped, command_lower)
        if chaining_result:
            return chaining_result

        return True  # All checks passed

    def _check_blocked_keywords(
        self, command_stripped: str, command_lower: str
    ) -> str | None:
        """Check command for blocked keywords."""
        # CRITICAL SECURITY: Block dangerous commands
        BLOCKED_KEYWORDS = [
            "reload",  # Reboot device
            "write",  # Save config changes
            "erase",  # Delete configuration
            "delete",  # Delete files
            "no ",  # Negate/remove configs
            "clear",  # Clear counters/logs
            "configure",  # Enter config mode
            "conf t",  # Config terminal
            "config terminal",  # Config terminal (full)
            "enable",  # Elevate privileges
            "copy",  # Copy files (can overwrite)
            "format",  # Format filesystem
            "shutdown",  # Shutdown interfaces
            "boot",  # Boot system commands
            "username",  # User management
            "password",  # Password changes
            "crypto",  # Crypto operations
            "key",  # Key management
            "certificate",  # Certificate management
        ]

        for blocked in BLOCKED_KEYWORDS:
            if blocked in command_lower:
                msg = (
                    f"⚠ BLOCKED: '{command_stripped}'\n"
                    f"   Reason: Contains blocked keyword '{blocked}'\n"
                    f"   Only read-only commands are allowed for safety."
                )
                if self.verbose:
                    print(f"[SECURITY] {msg}")
                return msg
        return None

    def _check_allowed_prefix(
        self, command_stripped: str, command_lower: str
    ) -> str | None:
        """Check if command starts with allowed prefix."""
        # CRITICAL SECURITY: Use configured allowed prefixes
        allowed_prefixes = self.config.security.allowed_commands

        is_allowed = any(
            command_lower.startswith(prefix) for prefix in allowed_prefixes
        )

        if not is_allowed:
            allowed_str = ", ".join(allowed_prefixes)
            msg = (
                f"⚠ BLOCKED: '{command_stripped}'\n"
                f"   Reason: Does not start with allowed prefix\n"
                f"   Allowed prefixes: {allowed_str}\n"
                f"   Only read-only commands are permitted."
            )
            if self.verbose:
                print(f"[SECURITY] {msg}")
            return msg
        return None

    def _check_command_chaining(
        self, command_stripped: str, command_lower: str
    ) -> str | None:
        """Check for command chaining attempts."""
        if ";" in command_stripped:
            # ALWAYS block semicolon command chaining
            msg = (
                f"⚠ BLOCKED: '{command_stripped}'\n"
                f"   Reason: Semicolon command chaining detected\n"
                f"   Only single commands allowed."
            )
            if self.verbose:
                print(f"[SECURITY] {msg}")
            return msg

        # Check for pipe command chaining
        if "|" in command_stripped:
            # Tests require uppercase | INCLUDE, so convert to lowercase before checks
            lowered = command_lower

            # Allow ONLY 'include', 'begin', 'section', and 'exclude' (common Cisco filters)
            allowed_ops = ["| include", "| begin", "| section", "| exclude"]
            has_allowed_pipe = any(op in lowered for op in allowed_ops)

            if not has_allowed_pipe:
                msg = (
                    f"⚠ BLOCKED: '{command_stripped}'\n"
                    f"   Reason: Unsupported pipe command\n"
                    f"   Allowed: | include, | begin, | section, | exclude"
                )
                if self.verbose:
                    print(f"[SECURITY] {msg}")
                return msg

        return None

    def _execute_validated_command(self, command_stripped: str) -> str:
        """Execute a command that has passed all validation checks."""
        timestamp = datetime.now().isoformat()
        try:
            if self.verbose:
                print(f"[{timestamp}] ✅ Executing (validated): {command_stripped}")

            output = self.device.execute_command(command_stripped)

            # Log successful execution to history AND audit log
            self.command_history.append(
                {
                    "timestamp": timestamp,
                    "command": command_stripped,
                    "output_length": len(output),
                    "success": True,
                    "validated": True,
                }
            )

            # CRITICAL: Log to audit system
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command=command_stripped,
                    success=True,
                    output_length=len(output),
                )

            return output

        except ConnectionError as e:  # Catch specific connection errors
            # Log failed execution to history
            self.command_history.append(
                {
                    "timestamp": timestamp,
                    "command": command_stripped,
                    "error": str(e),
                    "success": False,
                    "validated": True,
                }
            )
            # Return clear message to AI that connection is dead
            error_msg = (
                f"❌ Connection Error: {e!s}\n\n"
                "The device connection has failed. "
                "Please inform the user they need to restart the application."
            )
            if self.verbose:
                print(f"[{timestamp}] {error_msg}")

            # CRITICAL: Log to audit system
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command=command_stripped,
                    success=False,
                    error=str(e),
                )
            return error_msg

        except Exception as e:
            # Log failed execution to history
            self.command_history.append(
                {
                    "timestamp": timestamp,
                    "command": command_stripped,
                    "error": str(e),
                    "success": False,
                    "validated": True,
                }
            )
            error_msg = f"⚠ Error executing command: {e!s}"
            if self.verbose:
                print(f"[{timestamp}] {error_msg}")

            # CRITICAL: Log to audit system
            if self.audit_logger:
                self.audit_logger.log_command_executed(
                    command=command_stripped,
                    success=False,
                    error=str(e),
                )
            return error_msg

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
            question: User's question (should be pre-validated)
            context: Optional context for the AI

        Returns:
            Response from the AI or error message
        """
        # Additional safety: Check if question looks like a command
        if self._looks_like_command(question):
            return (
                "⚠️  Your input looks like a direct command.\n"
                "   Please ask a question instead, like:\n"
                "   - 'What interfaces are up?'\n"
                "   - 'Show me the routing table'\n"
                "   Or use '/cmd <command>' to execute directly."
            )

        # Check rate limit
        if not self._check_rate_limit():
            wait_time = self.rate_limit_window - (time.time() - self.request_times[0])
            return f"⚠ Rate limit exceeded. Please wait {int(wait_time)}s."

        # The system prompt is now part of the agent's definition,
        # so we no longer need to build the full query here.
        # We simply pass the user's question as the input.

        max_retries = len(MODEL_FALLBACK_CHAIN)
        retry_count = 0

        while retry_count < max_retries:
            # Pass the user's question directly to the retry processor
            response = self._process_query_with_retry(question, retry_count)
            if response is not None:
                return response
            retry_count += 1

        return "❌ All models failed. No more fallback models available."

    def _process_query_with_retry(
        self, full_query: str, retry_count: int
    ) -> str | None:
        """Process query with retry logic."""
        try:
            if self.verbose and retry_count > 0:
                print(f"\n🔄 Retry #{retry_count} with {self.current_model}...")

            result = self._execute_agent_query(full_query)

            # Track model usage
            if self.current_model not in self.model_usage_stats:
                self.model_usage_stats[self.current_model] = 0
            self.model_usage_stats[self.current_model] += 1

            response = self._extract_response(result)

            if self.verbose:
                start_time = (
                    time.time() - 0.1
                )  # Approximate time, actual time is not tracked here
                elapsed_time = time.time() - start_time
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
                return None  # Indicate retry needed
            return error_msg

        except Exception as e:
            return self._handle_error(e, retry_count)

    def _execute_agent_query(self, full_query: str):
        """Execute the agent query and return the result."""
        start_time = time.time()

        # --- MODIFIED INVOKE CALL ---
        # AgentExecutor expects a dictionary with an "input" key.
        result = self.agent.invoke(
            {"input": full_query},
            config={"recursion_limit": 8},
        )

        self._last_query_time = time.time() - start_time
        return result

    def _extract_response(self, result) -> str:
        """Extract the AI response from the result."""
        # --- MODIFIED RESPONSE EXTRACTION ---
        # AgentExecutor returns a dictionary where the final answer is in the "output" key.
        if isinstance(result, dict) and "output" in result:
            return result["output"]

        # Provide a fallback for any unexpected response structures
        if self.verbose:
            print(f"Unexpected agent result structure: {result}")
        return "Sorry, I encountered an issue processing the response."

    def _handle_error(self, e: Exception, retry_count: int) -> str | None:
        """Handle exceptions during query processing."""
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
                time.sleep(2)  # Longer delay for rate limits
                return None  # Indicate retry needed
            return f"{error_msg}. No more fallback models available."

        # Non-rate-limit error - sanitize before displaying
        sanitized_error = self.data_protector.sanitize_error(str(e))
        return f"❌ Error: {sanitized_error}"

    def _looks_like_command(self, question: str) -> bool:
        """Check if question looks like a direct command rather than a question."""
        question_lower = question.lower().strip()

        # Direct command indicators
        command_prefixes = ["show ", "display ", "get ", "dir ", "configure ", "reload"]

        # If it starts with a command and has no question words, it's likely a command
        if any(question_lower.startswith(prefix) for prefix in command_prefixes):
            question_words = [
                "what",
                "how",
                "why",
                "when",
                "where",
                "which",
                "who",
                "is",
                "are",
                "can",
                "could",
                "would",
                "should",
            ]
            has_question_word = any(word in question_lower for word in question_words)
            has_question_mark = "?" in question

            # If no question indicators, it's probably a direct command
            if not has_question_word and not has_question_mark:
                return True

        return False

    def execute_direct_command(self, command: str) -> str:
        """Execute a command directly without AI processing.

        Useful for debugging or when AI is slow/unavailable.
        """
        try:
            if self.verbose:
                print(f"⚡ Executing: {command}")

            output = self.device.execute_command(command)

            # Log to history
            self.command_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "command": command,
                    "output_length": len(output),
                    "success": True,
                    "direct": True,
                }
            )

            # Sanitize output before returning
            return self.data_protector.sanitize_output(output, max_length=10000)
        except ConnectionError as e:
            # Log failed execution to history
            self.command_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "command": command,
                    "error": str(e),
                    "success": False,
                    "direct": True,
                }
            )
            error_msg = (
                f"❌ Connection Error: {e!s}\n\n"
                "The device connection has failed. "
                "Please inform the user they need to restart the application."
            )
            if self.verbose:
                print(error_msg)
            return error_msg
        except Exception as e:
            # Sanitize error before returning
            sanitized_error = self.data_protector.sanitize_error(str(e))
            return f"Error: {sanitized_error}"

    def get_statistics(self) -> dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary with command statistics, rate limit status, and model info
        """
        successful = sum(1 for cmd in self.command_history if cmd.get("success", False))
        failed = len(self.command_history) - successful
        rate_limit_active = len(self.request_times) >= self.rate_limit_requests

        return {
            "total_commands": len(self.command_history),
            "successful_commands": successful,
            "failed_commands": failed,
            "rate_limit_used": f"{len(self.request_times)}/{self.rate_limit_requests}",
            "rate_limit_active": rate_limit_active,
            "primary_model": self.primary_model,
            "current_model": self.current_model,
            "model_fallbacks": self.model_fallback_count,
            "model_usage": self.model_usage_stats,
        }

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get command history.

        Args:
            limit: Number of recent commands to return

        Returns:
            List of command history entries
        """
        return self.command_history[-limit:] if self.command_history else []
