"""Simplified main entry point for the AI Network Agent using Typer for a clean CLI.

This module serves as the entry point for the simplified application, providing
a 'chat' command for interactive sessions with the AI network agent.
"""

import os
import typer
from dotenv import load_dotenv
from src.agents.simple_agent import SimpleNetworkAgent
from src.core.config import settings


# Create a Typer app
app = typer.Typer(help="Simplified AI Network Agent")


@app.command()
def chat():
    """Starts an interactive chat session with the network agent.

    This command initializes the simplified network agent,
    then enters an interactive loop to process user queries. The process
    involves LLM-based interpretation of natural language requests
    and execution of appropriate network commands.
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
                question = input("\n💬 You: ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not question:
                continue
            if question.lower() in ["quit", "exit"]:
                break

            print("-" * 40)
            try:
                # Process the request with the simplified agent
                result = agent.process_request(question)

                print(f"\n🖥️  Device: {result['device_name']}")
                print(f"🔍 Command: {result['command']}")
                print(f"\n📋 Output:\n{result['output']}")
            except KeyboardInterrupt:
                print("\n⚠️  Operation interrupted by user. Cleaning up connections...")
                agent.close_sessions()
                break
            except Exception as e:
                print(f"❌ An unexpected error occurred: {e}")
            print("-" * 40)
    finally:
        agent.close_sessions()
        print("\n👋 All network sessions closed. Goodbye!")


if __name__ == "__main__":
    app()
