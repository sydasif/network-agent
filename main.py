"""
AI Agent for Network Devices - LangChain Edition
Talk to multiple network devices using natural language with LangChain agents!
"""

import os
from pathlib import Path

from src.agents.network_agent import NetworkAgent
from src.agents.device_agent import DeviceAgent
from src.agents.inventory_agent import InventoryAgent
from src.agents.router_agent import RouterAgent
from src.tools.execute_show import ExecuteShowTool
from src.tools.device_session_tools import DeviceSessionTools
from src.tools.inventory_tools import InventoryTools
from src.tools.validation_tools import ValidationTools
from src.tools.sensitive_data_tool import SensitiveDataTool
from src.tools.device_router import DeviceRouterTool
from src.command_executor import CommandExecutor
from src.device_manager import DeviceManager
from src.inventory import InventoryManager
from src.validation import ValidationPipeline
from src.device_router import DeviceRouter
from src.audit import AuditLogger
from src.settings import settings
from src.utils import print_formatted_header
from src.console import Console


def main():
    """Main entry point using new LangChain agent architecture."""
    print_formatted_header("AI Network Agent - LangChain Edition")
    
    # Initialize core components
    audit_logger = AuditLogger(
        log_dir=settings.log_directory,
        enable_console=settings.enable_console_logging,
        enable_file=settings.enable_file_logging,
        log_level=settings.log_level,
    )
    
    # Initialize inventory manager
    inventory_file = "inventory.yaml"
    inventory_path = Path(inventory_file)
    if not inventory_path.exists():
        print(Console.warning(f"⚠️  Inventory file not found: {inventory_file}"))
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
        print(Console.info(f"📦 Created sample inventory file: {inventory_file}"))
    
    inventory_manager = InventoryManager(inventory_file)
    
    # Initialize device manager
    device_manager = DeviceManager()
    
    # Initialize device router
    device_router = DeviceRouter(device_manager, inventory_manager)
    
    # Initialize validation pipeline
    validation_pipeline = ValidationPipeline(audit_logger)
    
    # Initialize command executor
    command_executor = CommandExecutor(audit_logger)
    
    # Create tool instances with dependencies
    execute_show_tool = ExecuteShowTool(command_executor, device_manager).create_tool()
    
    device_session_tools = DeviceSessionTools(device_manager, inventory_manager)
    connect_device_tool = device_session_tools.create_connect_device_tool()
    switch_device_tool = device_session_tools.create_switch_device_tool()
    disconnect_device_tool = device_session_tools.create_disconnect_device_tool()
    get_current_device_tool = device_session_tools.create_get_current_device_tool()
    
    inventory_tools = InventoryTools(inventory_manager)
    get_inventory_tool = inventory_tools.create_get_inventory_tool()
    search_inventory_tool = inventory_tools.create_search_inventory_tool()
    get_device_info_tool = inventory_tools.create_get_device_info_tool()
    
    validation_tools = ValidationTools(validation_pipeline)
    validate_query_tool = validation_tools.create_validate_query_tool()
    sanitize_query_tool = validation_tools.create_sanitize_query_tool()
    validate_command_tool = validation_tools.create_validate_command_tool()
    
    sensitive_data_tool = SensitiveDataTool().create_sanitize_output_tool()
    
    device_router_tool = DeviceRouterTool(device_router)
    extract_device_tool = device_router_tool.create_extract_device_tool()
    route_to_device_tool = device_router_tool.create_route_to_device_tool()
    
    # Collect all tools for the main network agent
    all_tools = [
        execute_show_tool,
        connect_device_tool,
        switch_device_tool,
        disconnect_device_tool,
        get_current_device_tool,
        get_inventory_tool,
        search_inventory_tool,
        get_device_info_tool,
        validate_query_tool,
        sanitize_query_tool,
        validate_command_tool,
        sensitive_data_tool,
        extract_device_tool,
        route_to_device_tool,
    ]
    
    # Initialize the main network agent
    network_agent = NetworkAgent(
        groq_api_key=settings.groq_api_key,
        model_name=settings.model_name,
        temperature=settings.temperature,
        timeout=settings.api_timeout,
        tools=all_tools
    )
    
    print(Console.success(f"🤖 Network agent initialized with {len(all_tools)} tools"))
    print(Console.success(f"📦 Inventory: {len(inventory_manager)} devices loaded"))
    
    # Simple command loop for demo
    print("\n💡 Tip: Ask naturally like 'show vlans on SW1' or 'check RTR1 uptime'")
    print("=" * 60)
    print("Ready! Ask questions about any device in your inventory")
    print("Type 'quit' to exit")
    print("=" * 60)
    
    while True:
        try:
            question = input(f"\n{Console.prompt(' 💬 Ask: ')}").strip()
        except (KeyboardInterrupt, EOFError):
            print(Console.info("\n\n👋 Exiting..."))
            break
            
        if question.lower() in ["quit", "exit", "q"]:
            break
            
        if not question:
            continue
            
        print("-" * 40)
        try:
            response = network_agent.run(question)
            print(f"\n{response}")
        except Exception as e:
            print(Console.error(f"❌ Error: {e}"))
        print("-" * 40)
    
    # Cleanup
    device_manager.disconnect_all()
    audit_logger.close()
    print(Console.info("👋 Session ended. Goodbye!"))


if __name__ == "__main__":
    main()