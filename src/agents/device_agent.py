"""Device-specific agent for network device operations."""

import logging
from typing import Optional, List
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


logger = logging.getLogger("net_agent.agents.device_agent")


class DeviceAgent:
    """Agent focused on device-specific operations."""
    
    def __init__(
        self,
        groq_api_key: str,
        model_name: str = "llama-3.3-70b",
        temperature: float = 0.1,
        timeout: int = 60,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the device agent."""
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
        
        # Set up device-specific tools
        self.tools = tools or []
        
        # Define system prompt for device operations
        system_prompt = """You are an expert network device operator.
        You focus specifically on connecting to, configuring, and troubleshooting individual network devices.
        You have access to tools that can connect to devices, switch between them, run show commands, and validate command safety.
        
        Always connect to a device before running commands on it.
        Always validate commands before executing them.
        When switching devices, ensure the target device is connected first.
        
        Provide clear and concise feedback on device operations."""
        
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
            max_iterations=8,
            max_execution_time=timeout
        )
        
        logger.info(f"Device agent initialized with {len(self.tools)} tools")

    def run(self, query: str) -> str:
        """Run the agent with a device-specific query."""
        logger.info(f"Processing device query: {query}")
        try:
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            logger.error(f"Error running device agent: {e}")
            return f"Error processing device query: {str(e)}"