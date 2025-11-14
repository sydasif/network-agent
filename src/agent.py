"""Agent setup and management for network automation."""

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from .network_device import DeviceConnection


class Agent:
    """AI-powered agent for network automation."""

    def __init__(self, groq_api_key: str, device: DeviceConnection):
        """Initialize the agent."""
        self.device = device

        # Set up the AI model
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
        )

        # Create a tool the AI can use to run commands
        self.execute_command_tool = tool("execute_show_command")(
            self._execute_device_command
        )

        # Create the AI agent with the tool
        self.agent = create_react_agent(self.llm, [self.execute_command_tool])

    def _execute_device_command(self, command: str) -> str:
        """Execute a command on the device (used by AI)."""
        return self.device.execute_command(command)

    def answer_question(self, question: str) -> str:
        """Answer a question about the device."""
        # Give the AI instructions
        prompt = f"""You are a network engineer assistant.
Use the execute_show_command tool to run network commands.
Answer the user's question clearly and concisely, and format outputs in summary style.

User question: {question}"""

        try:
            result = self.agent.invoke({"messages": [("user", prompt)]})

            # Extract the AI's response
            last_message = result["messages"][-1]
            return last_message.content
        except Exception as e:
            return f"Error: {str(e)}"
