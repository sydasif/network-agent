"""Defines the Tool Executor for the LangGraph workflow.

This module implements the tool executor component that takes a plan from the
Planner agent and executes the specified tool calls. It serves as an interface
between the agent workflow and the actual network tools.
"""

from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from src.tools.inventory import inventory_search
from src.tools.executor import run_network_command
from src.tools.ping_tool import ping_host

# Map tool names to their functions
TOOLS = {
    "inventory_search": inventory_search,
    "run_network_command": run_network_command,
    "ping_host": ping_host,
}


def tool_executor(plan: List[Dict[str, Any]]) -> List[Any]:
    """Executes a list of tool calls from the planner's plan.

    This function takes a plan consisting of tool calls and executes them sequentially.
    Each tool call in the plan specifies a tool name and arguments to pass to the tool.
    The function handles both successful execution and error cases.

    The function detects whether the plan is a simple list of steps or has a "steps" key
    containing the list of steps, and processes accordingly.

    Args:
        plan (List[Dict[str, Any]]): A list of tool call dictionaries or a dictionary
            containing a "steps" key with the list of tool call dictionaries.

    Returns:
        List[Any]: A list of results from each tool call execution. Each result will
        be either the output of the tool or an error message string if the tool
        execution failed or if the tool name is unknown.
    """
    # Detect if the plan is in the new format with "steps" key
    if isinstance(plan, dict) and "steps" in plan:
        steps = plan.get("steps", [])
    else:
        # Assume it's the old format - a list of steps
        steps = plan if isinstance(plan, list) else []

    results = []
    for step in steps:
        tool_name = step.get("tool")
        tool_args = step.get("args", {})

        if tool_name in TOOLS:
            tool_function = TOOLS[tool_name]
            try:
                # Check if the tool is a LangChain tool or a regular Python function
                if isinstance(tool_function, BaseTool):
                    result = tool_function.invoke(tool_args)
                else:
                    # For regular Python functions, call directly with the arguments
                    result = tool_function(**tool_args)

                # Clean double layered output by flattening nested result structures
                # If result has a 'result' key containing another 'result', flatten it
                if isinstance(result, dict) and "result" in result:
                    if isinstance(result["result"], dict) and "result" in result["result"]:
                        # Double nested: {"result": {"result": "actual_output"}}
                        result = result["result"]["result"]
                    elif isinstance(result["result"], (str, int, float, bool, list, dict)):
                        # Single nested: {"result": "actual_output"}
                        result = result["result"]

                results.append(result)
            except Exception as e:
                results.append(f"Error executing tool {tool_name}: {e}")
        else:
            results.append(f"Unknown tool: {tool_name}")

    return results
