"""Network agent with LangChain tools for network automation."""

import logging
from typing import Annotated, Optional, List
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import TypedDict


logger = logging.getLogger("net_agent.agents.network_agent")


class NetworkAgent:
    """Main network automation agent using LangChain tools."""
    
    def __init__(
        self,
        groq_api_key: str,
        model_name: str = "llama-3.3-70b",
        temperature: float = 0.1,
        timeout: int = 60,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the network agent."""
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
        
        # Set up tools if provided
        self.tools = tools or []
        
        # Define system prompt
        system_prompt = """You are an expert network engineer assistant. 
        You help users with network device management, configuration, and troubleshooting.
        You have access to tools that can connect to devices, execute commands, and retrieve inventory information.
        
        When a user wants to run a command, always make sure to connect to the appropriate device first.
        If the user doesn't specify a device, look for it in the inventory or ask for clarification.
        
        Always validate commands before executing them.
        Be precise and helpful in your responses."""
        
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
            max_iterations=10,
            max_execution_time=timeout
        )
        
        logger.info(f"Network agent initialized with {len(self.tools)} tools")

    def run(self, query: str) -> str:
        """Run the agent with a user query."""
        logger.info(f"Processing query: {query}")
        try:
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return f"Error processing query: {str(e)}"