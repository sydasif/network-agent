import os
from contextlib import contextmanager, redirect_stderr, redirect_stdout

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.tools.executor import run_network_command
from src.tools.inventory import inventory_search
from src.tools.parser import parse_network_output


# ===================================================================
# SYSTEM PROMPT (IMPROVED)
# ===================================================================
SYSTEM_PROMPT = """
You are a network engineer assistant. Follow these rules precisely:

TOOL SELECTION RULES:
1. Use "inventory_search" ONLY when the user asks to:
   - List all devices
   - Search for a device by name
   - Get device information
   Examples: "list devices", "find D1", "show me all switches"

2. Use "run_network_command" when the user asks to:
   - Execute ANY network CLI command
   - Get device status, configuration, or operational data
   - Show vlans, interfaces, version, etc.
   Examples: "show vlans on D1", "check D2 interfaces", "get running config"

3. Use "parse_network_output" IMMEDIATELY after run_network_command returns output
   - Take the EXACT output from run_network_command
   - Pass it to parse_network_output
   - Then provide a human-friendly answer

EXECUTION FLOW:
For network commands: run_network_command → parse_network_output → answer user
For device info: inventory_search → answer user

MULTI-DEVICE QUERIES:
If the user asks about multiple devices (e.g., "show IP on D1 and D2"):
- Explain that you can only query one device at a time
- Ask which device they want to check first
- DO NOT attempt to call run_network_command multiple times

CRITICAL RULES:
- Your final answer MUST be natural language plain text
- DO NOT output tool syntax like function=... or JSON
- DO NOT call run_network_command more than once per query
- DO NOT call parse_network_output more than once per query
- ALWAYS provide a final answer after using tools
- If a query doesn't need tools, answer directly
- Never loop tool calls
- After calling parse_network_output, ALWAYS interpret and summarize the results for the user
- If you cannot execute a query, explain why clearly and suggest alternatives
"""

# ===================================================================
# PROMPT TEMPLATE
# ===================================================================
prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{input}"), ("ai", "{agent_scratchpad}")]
)


# ===================================================================
# UTILITY: Suppress all output
# ===================================================================
@contextmanager
def suppress_output():
    """Suppress both stdout and stderr."""
    with open(os.devnull, "w") as devnull:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            yield


# ===================================================================
# MAIN AGENT
# ===================================================================
class NetworkAgent:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(
            groq_api_key=api_key, model_name="llama-3.1-8b-instant", temperature=0.0
        )

        # 3-Tool Architecture
        self.tools = [inventory_search, run_network_command, parse_network_output]

        # Agent with correct prompt + tool call support
        self.agent = AgentExecutor(
            agent=create_tool_calling_agent(self.llm, self.tools, prompt),
            tools=self.tools,
            return_intermediate_steps=True,
            max_iterations=5,
            handle_parsing_errors=True,
            verbose=False,
        )

    def run(self, query: str):
        try:
            # Suppress all LangChain verbose output
            with suppress_output():
                result = self.agent.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"⚠️ Agent error: {e!s}"
