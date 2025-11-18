"""Main entry point for the AI Network Agent using Typer for a clean CLI.

This module serves as the entry point for the application and provides two main
commands: 'chat' for interactive sessions and 'analyze' for on-demand network health
analysis. It handles environment loading, initializes the system components,
and orchestrates the entire workflow from user input to response generation.
"""
import os
import time
from pathlib import Path
from functools import lru_cache
import typer
import yaml
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from src.graph.workflow import NetworkWorkflow
from src.tools.inventory import network_manager
from src.core.config import settings
from src.core.state_manager import StateManager
from src.agents.analyzer import ProactiveAnalyzer
from src.core.health_monitor import HealthMonitor


# Create a Typer app
app = typer.Typer(help="AI Network Agent - NLP-First Co-pilot")


@app.command()
def chat():
    """Starts an interactive chat session with the network agent.

    This command initializes the network workflow,
    then enters an interactive loop to process user queries. The process
    involves LLM-based preprocessing, intent classification, and execution of
    the appropriate agent workflow to generate responses.
    """
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
                # Execute Agentic Workflow with raw query (the workflow now handles NLP internally)
                response = workflow.run(question, chat_history)

                print(f"\n🤖 Agent: {response}")
                chat_history.append(HumanMessage(content=question))
                chat_history.append(AIMessage(content=response))
            except KeyboardInterrupt:
                print("\n⚠️  Operation interrupted by user. Cleaning up connections...")
                network_manager.close_all_sessions()
                break
            except Exception as e:
                print(f"❌ An unexpected error occurred: {e}")
            print("-" * 40)
    finally:
        network_manager.close_all_sessions()
        print("\n👋 All network sessions closed. Goodbye!")


@lru_cache(maxsize=1)
def _get_cached_health_checks():
    """Caches the health checks to avoid repeated operations."""
    # Default set of health checks that were previously in command.yaml
    return [
        {"command": "show version", "description": "Device version and status"},
        {"command": "show interfaces", "description": "Interface status and statistics"},
        {"command": "show ip route", "description": "Routing table information"},
        {"command": "show processes cpu", "description": "CPU utilization"},
        {"command": "show memory", "description": "Memory utilization"}
    ]


@app.command()
def analyze():
    """Runs a single, on-demand health analysis across all devices.

    This command performs proactive health analysis by comparing current device
    states with previously stored snapshots. It executes a series of default
    health check commands and uses an LLM to analyze changes and determine
    their operational significance (Critical, Warning, or Informational).
    """
    load_dotenv()
    print("🤖 AI Network Agent - On-Demand Health Analysis")
    print("=" * 60)

    groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
    if not groq_api_key:
        print("⚠️ GROQ_API_KEY not set!")
        return

    state_manager = StateManager()
    analyzer = ProactiveAnalyzer(api_key=groq_api_key)

    health_checks = _get_cached_health_checks()

    if not health_checks:
        print("❌ No health checks defined. Exiting.")
        return

    print(f"📈 Analyzing {len(network_manager.devices)} devices with {len(health_checks)} checks...")
    print("-" * 40)

    try:
        for device in network_manager.devices.values():
            print(f"Device: {device.name}")
            for check in health_checks:
                command = check["command"]
                try:
                    current_output = network_manager.execute_command(device.name, command)
                    current_state = {"output": current_output}

                    # Use the analyzer's built-in snapshot storage functionality
                    analysis = analyzer.analyze_with_snapshot_storage(device.name, command, current_state)
                    significance = analysis['significance']
                    summary = analysis['summary']
                    print(f"  - Check '{command}': [{significance}] {summary}")

                except KeyboardInterrupt:
                    print("\n⚠️  Analysis interrupted by user. Cleaning up connections...")
                    network_manager.close_all_sessions()
                    print("❌ Analysis interrupted.")
                    return  # Exit the function early
                except Exception as e:
                    print(f"  - Check '{command}': [Error] {e}")
        print("✅ Analysis complete.")
    finally:
        # Ensure sessions are closed on all paths (success, error, or interrupt)
        network_manager.close_all_sessions()


# Global health monitor instance
health_monitor = None


@app.command()
def monitor(interval: int = 900):
    """Starts the continuous health monitoring service.

    This command starts a daemon process that continuously monitors network devices
    according to the default health checks, running checks at the specified interval.

    Args:
        interval (int): Interval between health checks in seconds (default: 900 = 15min)
    """
    load_dotenv()
    print("🤖 AI Network Agent - Continuous Health Monitor")
    print("=" * 60)

    groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
    if not groq_api_key:
        print("⚠️ GROQ_API_KEY not set!")
        return

    if not Path(settings.inventory_file).exists():
        print(f"⚠️ Inventory file '{settings.inventory_file}' not found. Please create one.")
        return
    print(f"📦 Inventory loaded: {len(network_manager.devices)} devices found.")

    global health_monitor
    try:
        health_monitor = HealthMonitor(api_key=groq_api_key)
        health_monitor.start_monitoring(interval=interval)

        print(f"📊 Health monitor running with {len(health_monitor.health_checks)} checks")
        print("Press Ctrl+C to stop the monitor...")

        # Keep the main thread alive to allow the monitor to run
        try:
            while health_monitor.health_running:
                time.sleep(1)  # Check every second if the monitor is still running
        except KeyboardInterrupt:
            print("\n⚠️  Health monitor interrupted by user.")
            stop_monitor()

    except Exception as e:
        print(f"❌ Error starting health monitor: {e}")
        return


def stop_monitor():
    """Stops the health monitoring service gracefully."""
    global health_monitor
    if health_monitor:
        health_monitor.stop_monitoring()
        health_monitor = None
        print("✅ Health monitor service stopped gracefully.")


if __name__ == "__main__":
    app()
