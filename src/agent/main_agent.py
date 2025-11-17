"""Main network agent implementation."""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_groq import ChatGroq

from src.tools.executor import run_network_command
from src.tools.inventory import inventory_search
from src.tools.parser import parse_network_output


class NetworkAgent:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(
            groq_api_key=api_key, model_name="llama-3.3-70b", temperature=0.1
        )

        self.tools = [inventory_search, run_network_command, parse_network_output]

        self.agent = AgentExecutor(
            agent=create_tool_calling_agent(self.llm, self.tools),
            tools=self.tools,
            max_iterations=5,
            handle_parsing_errors=True,
        )

    def run(self, query: str):
        return self.agent.invoke({"input": query})["output"]
