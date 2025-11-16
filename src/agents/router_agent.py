"""Router agent for routing and decision-making."""

import logging
from typing import Optional, List
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


logger = logging.getLogger("net_agent.agents.router_agent")


class RouterAgent:
    """Agent focused on routing decisions and query analysis."""
    
    def __init__(
        self,
        groq_api_key: str,
        model_name: str = "llama-3.3-70b",
        temperature: float = 0.1,
        timeout: int = 60,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the router agent."""
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
        
        # Set up routing-specific tools
        self.tools = tools or []
        
        # Define system prompt for routing operations
        system_prompt = """You are an expert network query analyzer and router.
        Your primary role is to analyze user queries and determine what actions are needed.
        You extract device names from queries, identify what type of information is requested, 
        and determine which tools need to be used.
        
        When you receive a query, first analyze it to identify:
        1. Which device(s) the query refers to (if any)
        2. What type of information or action is requested
        3. What tools might be needed to fulfill the request
        
        Be precise in your analysis and routing decisions."""
        
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
        
        logger.info(f"Router agent initialized with {len(self.tools)} tools")

    def run(self, query: str) -> str:
        """Run the agent with a routing-specific query."""
        logger.info(f"Processing routing query: {query}")
        try:
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            logger.error(f"Error running router agent: {e}")
            return f"Error processing routing query: {str(e)}"