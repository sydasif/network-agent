"""
AI Agent for Network Devices - Simple Version
Talk to your Cisco router using natural language!
"""

import getpass
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from netmiko import ConnectHandler


class NetworkAgent:
    """AI-powered network device assistant."""

    def __init__(self, groq_api_key: str):
        """Initialize the AI agent."""
        # Set up the AI model
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        self.connection = None

        # Create a tool the AI can use to run commands
        self.execute_command_tool = tool("execute_show_command")(self._execute_command)

        # Create the AI agent with the tool
        self.agent = create_react_agent(self.llm, [self.execute_command_tool])

    def connect(self, hostname: str, username: str, password: str):
        """Connect to a network device."""
        device_config = {
            'device_type': 'cisco_ios',
            'host': hostname,
            'username': username,
            'password': password,
            'timeout': 30,
        }
        self.connection = ConnectHandler(**device_config)
        print(f"✓ Connected to {hostname}")

    def disconnect(self):
        """Disconnect from the device."""
        if self.connection:
            self.connection.disconnect()
            print("✓ Disconnected")

    def _execute_command(self, command: str) -> str:
        """Execute a command on the device (used by AI)."""
        if not self.connection:
            return "Error: Not connected to device"

        try:
            output = self.connection.send_command(command)
            return output
        except Exception as e:
            return f"Error: {str(e)}"

    def ask(self, question: str) -> str:
        """Ask the AI a question about the device."""
        # Give the AI instructions
        prompt = f"""You are a network engineer assistant.
Use the execute_show_command tool to run Cisco commands.
Answer the user's question clearly and concisely, and provide a formatted summary if applicable.


User question: {question}"""

        try:
            result = self.agent.invoke({"messages": [("user", prompt)]})

            # Extract the AI's response
            last_message = result["messages"][-1]
            return last_message.content
        except Exception as e:
            return f"Error: {str(e)}"


def main():
    """Main program."""
    load_dotenv()

    print("=" * 60)
    print("AI Network Agent")
    print("=" * 60)

    # Get connection details
    hostname = input("\nDevice IP: ").strip()
    username = input("Username: ").strip()
    password = os.getenv('DEVICE_PASSWORD') or getpass.getpass("Password: ")

    # Get API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("Error: Set GROQ_API_KEY in .env file")
        return

    # Create and connect agent
    agent = NetworkAgent(api_key)

    try:
        agent.connect(hostname, username, password)

        print("\n" + "=" * 60)
        print("Ready! Type 'quit' to exit")
        print("=" * 60 + "\n")

        # Chat loop
        while True:
            question = input("\n💬 Ask: ").strip()

            if question.lower() in ['quit', 'exit']:
                break

            if not question:
                continue

            print("\n" + "-" * 60)
            answer = agent.ask(question)
            print(answer)
            print("-" * 60)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        agent.disconnect()


if __name__ == "__main__":
    main()
