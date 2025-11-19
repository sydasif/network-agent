"""Main entry point for the AI Network Agent CLI application.

This module provides a command-line interface for interacting with network devices
using natural language commands. It uses the Typer framework for CLI functionality
and integrates with a SimpleNetworkAgent to process user requests and execute
network commands on specified devices.
"""

import os
import typer
from dotenv import load_dotenv
from src.agents.simple_agent import SimpleNetworkAgent
from src.core.config import settings


app = typer.Typer()


@app.command()
def chat():
    """Starts an interactive chat session with the network agent.

    This function initializes the SimpleNetworkAgent with the GROQ API key,
    then enters an interactive loop to process user queries. The process
    involves LLM-based interpretation of natural language requests
    and execution of appropriate network commands on the specified devices.
    """
    load_dotenv()
    print("🤖 Simplified AI Network Agent - Interactive Chat")
    print("=" * 60)

    groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
    if not groq_api_key:
        print("⚠️ GROQ_API_KEY not set! Please create a .env file with your key.")
        return

    try:
        agent = SimpleNetworkAgent(api_key=groq_api_key)
        print("✅ AI agent initialized successfully.")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return

    print("\n💡 Ask network questions like 'show interfaces on S1' or 'show version on R1'")
    print("   Type 'quit' or 'exit' to end the session.")
    print("=" * 60)

    try:
        while True:
            try:
                # Get user input for network command
                question = input("\n💬 You: ").strip()
            except (KeyboardInterrupt, EOFError):
                # Handle user interruption gracefully
                break

            if not question:
                # Skip empty input
                continue
            question_lower = question.lower()
            if question_lower in ["quit", "exit"]:
                # Break the loop if user wants to exit
                break

            print("-" * 40)
            try:
                # Process the natural language request and execute command on device
                result = agent.process_request(question)

                print(f"\n🖥️  Device: {result['device_name']}")
                print(f"🔍 Command: {result['command']}")
                print(f"\n📋 Output:\n{result['output']}")
            except KeyboardInterrupt:
                # Handle interruption during command execution
                print("\n⚠️  Operation interrupted by user. Cleaning up connections...")
                agent.close_sessions()
                break
            except Exception as e:
                # Handle any other errors during command processing
                print(f"❌ An unexpected error occurred: {e}")
            print("-" * 40)
    finally:
        # Ensure all network sessions are closed even if an error occurs
        agent.close_sessions()
        print("\n👋 All network sessions closed. Goodbye!")


if __name__ == "__main__":
    app()
