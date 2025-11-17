"""Main entry point for the AI Network Agent using Typer for a clean CLI."""
import os
from pathlib import Path
import typer
import yaml
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from src.graph.workflow import NetworkWorkflow
from src.nlp.preprocessor import NLPPreprocessor
from src.tools.inventory import network_manager
from src.core.config import settings
from src.core.state_manager import StateManager
from src.agents.analyzer import ProactiveAnalyzer


# Create a Typer app
app = typer.Typer(help="AI Network Agent - NLP-First Co-pilot")


@app.command()
def chat():
    """Starts an interactive chat session with the network agent."""
    load_dotenv()
    print("🤖 AI Network Agent - Interactive Chat")
    print("=" * 60)

    groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
    if not groq_api_key:
        print("⚠️ GROQ_API_KEY not set! Please create a .env file with your key.")
        return

    if not Path(settings.inventory_file).exists():
        print(f"⚠️ Inventory file '{settings.inventory_file}' not found. Please create one.")
        return
    print(f"📦 Inventory loaded: {len(network_manager.devices)} devices found.")


    try:
        nlp_processor = NLPPreprocessor()
        workflow = NetworkWorkflow(api_key=groq_api_key)
        print("✅ NLP layer and Agent workflow initialized successfully.")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return

    print(
        "\n💡 Ask complex questions like 'show interfaces on S1' or 'show running config on R1'"
    )
    print("   Type 'quit' or 'exit' to end the session.")
    print("=" * 60)

    chat_history = []
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
            # 1. NLP Pre-processing
            structured_intent = nlp_processor.process(question)
            print(
                f"🔍 Intent: {structured_intent.intent} | Entities: {structured_intent.entities.model_dump(exclude_none=True)}"
            )

            # 2. Intelligent Routing
            if structured_intent.is_ambiguous:
                response = "I'm sorry, your request is a bit ambiguous. Could you please provide more details, like a specific device name?"
            elif structured_intent.intent == "greeting":
                response = "Hello! How can I help you with the network today?"
            elif structured_intent.intent == "unknown":
                response = (
                    "I'm not sure how to handle that request. Please try rephrasing."
                )
            else:
                # 3. Execute Agentic Workflow
                response = workflow.run(structured_intent, chat_history)

            print(f"\n🤖 Agent: {response}")
            chat_history.append(HumanMessage(content=question))
            chat_history.append(AIMessage(content=response))
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
        print("-" * 40)

    network_manager.close_all_sessions()
    print("\n👋 All network sessions closed. Goodbye!")


@app.command()
def analyze():
    """Runs a single, on-demand health analysis across all devices."""
    load_dotenv()
    print("🤖 AI Network Agent - On-Demand Health Analysis")
    print("=" * 60)

    groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
    if not groq_api_key:
        print("⚠️ GROQ_API_KEY not set!")
        return

    state_manager = StateManager()
    analyzer = ProactiveAnalyzer(api_key=groq_api_key)

    with open("command.yaml", "r") as f:
        health_checks = yaml.safe_load(f).get("health_checks", [])

    if not health_checks:
        print("❌ No health checks defined in command.yaml. Exiting.")
        return

    print(f"📈 Analyzing {len(network_manager.devices)} devices with {len(health_checks)} checks...")
    print("-" * 40)

    for device in network_manager.devices.values():
        print(f"Device: {device.name}")
        for check in health_checks:
            command = check["command"]
            try:
                current_state = {"output": network_manager.execute_command(device.name, command)}
                previous_state = state_manager.get_latest_snapshot(device.name, command)

                if previous_state:
                    analysis = analyzer.analyze_change(device.name, command, previous_state, current_state)
                    significance = analysis['significance']
                    summary = analysis['summary']
                    print(f"  - Check '{command}': [{significance}] {summary}")
                else:
                    print(f"  - Check '{command}': [Informational] First run, storing baseline state.")

                state_manager.save_snapshot(device.name, command, current_state)

            except Exception as e:
                print(f"  - Check '{command}': [Error] {e}")
        print("-" * 40)

    network_manager.close_all_sessions()
    state_manager.close()
    print("✅ Analysis complete.")


if __name__ == "__main__":
    app()
