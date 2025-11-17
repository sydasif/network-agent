from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.tools.executor import run_network_command
from src.tools.inventory import inventory_search
from src.tools.parser import parse_network_output


# ===================================================================
# SYSTEM PROMPT (FINAL)
# ===================================================================
SYSTEM_PROMPT = """
You are a network engineer assistant.

You MUST follow these rules:

1. Your final answer to the user must ALWAYS be natural language plain text.
2. Do NOT output tool-call syntax such as function=..., arguments=..., or JSON.
3. If you use run_network_command:
    - Wait for the tool output
    - Then call parse_network_output with that exact output
    - After parsing, give a final plain-text answer to the user
4. Do NOT call run_network_command more than once.
5. Do NOT call parse_network_output more than once.
6. If the user asks about devices (list, search), call inventory_search once.
7. If the query does not need a tool, answer directly.
8. Never loop tool calls.
"""

# ===================================================================
# PROMPT TEMPLATE (must contain agent_scratchpad)
# ===================================================================
prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{input}"), ("ai", "{agent_scratchpad}")]
)


# ===================================================================
# MAIN AGENT
# ===================================================================
class NetworkAgent:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(
            groq_api_key=api_key, model_name="llama-3.1-8b-instant", temperature=0.1
        )

        # 3-Tool Architecture
        self.tools = [inventory_search, run_network_command, parse_network_output]

        # Agent with correct prompt + tool call support
        self.agent = AgentExecutor(
            agent=create_tool_calling_agent(self.llm, self.tools, prompt),
            tools=self.tools,
            return_intermediate_steps=True,  # <-- REQUIRED so agent continues after tool call
            max_iterations=4,  # safe limit
            handle_parsing_errors=True,
            verbose=False,
        )

    def run(self, query: str):
        try:
            result = self.agent.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"⚠️ Agent error: {e!s}"
