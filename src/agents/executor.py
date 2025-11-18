"""Defines the Tool Executor for the LangGraph workflow.

This module implements the tool executor component that takes a plan from the
Planner agent and executes the specified tool calls. It serves as an interface
between the agent workflow and the actual network tools.
"""

from typing import List, Dict, Any
from src.tools.inventory import inventory_search
from src.tools.executor import run_network_command

# Map tool names to their functions
TOOLS = {
    "inventory_search": inventory_search,
    "run_network_command": run_network_command,
}


def tool_executor(plan: List[Dict[str, Any]]) -> List[Any]:
    """Executes a list of tool calls from the planner's plan.

    This function takes a plan consisting of tool calls and executes them sequentially.
    Each tool call in the plan specifies a tool name and arguments to pass to the tool.
    The function handles both successful execution and error cases.

    Args:
        plan (List[Dict[str, Any]]): A list of tool call dictionaries, each containing
            'tool' (str) and 'args' (dict) keys.

    Returns:
        List[Any]: A list of results from each tool call execution. Each result will
        be either the output of the tool or an error message string if the tool
        execution failed or if the tool name is unknown.
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
