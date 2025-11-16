"""Inventory agent for device inventory queries."""

import logging
from typing import Optional, List
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


logger = logging.getLogger("net_agent.agents.inventory_agent")


class InventoryAgent:
    """Agent focused on inventory management and queries."""
    
    def __init__(
        self,
        groq_api_key: str,
        model_name: str = "llama-3.3-70b",
        temperature: float = 0.1,
        timeout: int = 60,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the inventory agent."""
        self.groq_api_key = groq_api_key
        self.model_name = model_name
        self.temperature = temperature
        self.timeout = timeout
        
        # Initialize LLM
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model_name,
            temperature=temperature,
            request_timeout=timeout,
        )
        
        # Set up inventory-specific tools
        self.tools = tools or []
        
        # Define system prompt for inventory operations
        system_prompt = """You are an expert network inventory manager.
        You focus specifically on managing and querying device inventory information.
        You have access to tools that can list, search, and retrieve detailed information about network devices in the inventory.
        
        You can help users find specific devices, get device details, search for devices by criteria, and understand the network topology.
        
        Provide clear, organized information about network devices."""
        
        # Create the agent with a proper prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create the agent
        self.agent_runnable = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        # Create an agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent_runnable,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            max_execution_time=timeout
        )
        
        logger.info(f"Inventory agent initialized with {len(self.tools)} tools")

    def run(self, query: str) -> str:
        """Run the agent with an inventory-specific query."""
        logger.info(f"Processing inventory query: {query}")
        try:
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            logger.error(f"Error running inventory agent: {e}")
            return f"Error processing inventory query: {str(e)}"