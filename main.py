"""Simplified AI Agent for Network Devices - 3-Tool Architecture"""

import os
from pathlib import Path

from src.agent.main_agent import NetworkAgent
from src.core.inventory import InventoryManager


def main():
    """Main entry point for the simplified network agent."""
    print("🤖 AI Network Agent - Simplified 3-Tool Architecture")
    print("=" * 60)

    # Check for API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("⚠️  GROQ_API_KEY environment variable not set!")
        print("Please set it before running this application.")
        return

    # Check inventory file exists
    inventory_file = "inventory.yaml"
    inventory_path = Path(inventory_file)
    if not inventory_path.exists():
        print(f"⚠️  Inventory file not found: {inventory_file}")
        # Create a simple sample inventory
        sample_content = """# Network Device Inventory
devices:
  - name: R1
    hostname: 192.168.1.10
    username: admin
    password: lab
    device_type: cisco_ios
    description: Router 1
    role: core
  - name: SW1
    hostname: 192.168.1.11
    username: admin
    password: lab
    device_type: cisco_ios
    description: Switch 1
    role: access
"""
        with open(inventory_file, "w") as f:
            f.write(sample_content)
        print(f"📦 Created sample inventory file: {inventory_file}")

    # Initialize the simplified network agent
    try:
        agent = NetworkAgent(api_key=groq_api_key)
        print("✅ Network agent initialized successfully")

        # Load inventory to show device count
        inventory_manager = InventoryManager(inventory_file)
        print(f"📦 Inventory: {len(inventory_manager.devices)} devices loaded")

    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return

    print("\n💡 Tip: Ask naturally like 'show vlans on SW1' or 'check R1 uptime'")
    print("=" * 60)
    print("Ready! Ask questions about any device in your inventory")
    print("Type 'quit' to exit")
    print("=" * 60)

    while True:
        try:
            question = input("\n💬 Ask: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Exiting...")
            break

        if question.lower() in ["quit", "exit", "q"]:
            break

        if not question:
            continue

        print("-" * 40)
        try:
            response = agent.run(question)
            print(f"\n{response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 40)

    print("👋 Session ended. Goodbye!")


if __name__ == "__main__":
    main()
