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
    steps = _extract_steps_from_plan(plan)
    results = []

    for step in steps:
        tool_name = step.get("tool")
        tool_args = step.get("args", {})

        result = _execute_single_step(tool_name, tool_args)
        results.append(result)

    return results


def _extract_steps_from_plan(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extracts the list of steps from the plan, handling different format variants.

    The plan can come in two different formats:
    1. New format: {"steps": [list of tool calls]}
    2. Old format: [list of tool calls]

    Args:
        plan: The plan which may be a list of steps or a dict with 'steps' key

    Returns:
        A list of step dictionaries
    """
    # Detect if the plan is in the new format with "steps" key
    if isinstance(plan, dict) and "steps" in plan:
        return plan.get("steps", [])
    # Assume it's the old format - a list of steps
    return plan if isinstance(plan, list) else []


def _execute_single_step(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    """Executes a single tool step.

    Handles both LangChain tool objects and regular Python functions with the same interface,
    providing a unified execution mechanism for all tool types.

    Args:
        tool_name: The name of the tool to execute
        tool_args: The arguments to pass to the tool

    Returns:
        The result of the tool execution or an error message
    """
    if tool_name not in TOOLS:
        return f"Unknown tool: {tool_name}"

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
        return _flatten_nested_result(result)

    except Exception as e:
        return f"Error executing tool {tool_name}: {e}"


def _flatten_nested_result(result: Any) -> Any:
    """Flattens nested result structures by extracting nested 'result' values.

    This utility handles inconsistent result structures that may occur when
    different tool types return differently nested data structures. It handles:
    - Double nested results: {"result": {"result": "actual_output"}}
    - Single nested results: {"result": "actual_output"}
    - Non-nested results: direct value

    Args:
        result: The result to flatten

    Returns:
        The flattened result
    """
    if isinstance(result, dict) and "result" in result:
        if isinstance(result["result"], dict) and "result" in result["result"]:
            # Double nested: {"result": {"result": "actual_output"}}
            return result["result"]["result"]
        if isinstance(result["result"], (str, int, float, bool, list, dict)):
            # Single nested: {"result": "actual_output"}
            return result["result"]

    return result
