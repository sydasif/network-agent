"""Defines the Tool Executor for the LangGraph workflow."""
from typing import List, Dict, Any
from src.tools.inventory import inventory_search
from src.tools.executor import run_network_command
from src.tools.log_analyzer import analyze_logs

# Map tool names to their functions
TOOLS = {
    "inventory_search": inventory_search,
    "run_network_command": run_network_command,
    "analyze_logs": analyze_logs,
}

def tool_executor(plan: List[Dict[str, Any]]) -> List[Any]:
    """
    Executes a list of tool calls from the planner's plan.
    """
    results = []
    for step in plan:
        tool_name = step.get("tool")
        tool_args = step.get("args", {})

        if tool_name in TOOLS:
            tool_function = TOOLS[tool_name]
            try:
                result = tool_function.invoke(tool_args)
                results.append(result)
            except Exception as e:
                results.append(f"Error executing tool {tool_name}: {e}")
        else:
            results.append(f"Unknown tool: {tool_name}")

    return results