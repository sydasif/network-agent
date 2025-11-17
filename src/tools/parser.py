"""Parser tool for network output."""

from langchain_core.tools import tool


@tool
def parse_network_output(cli_output: str) -> str:
    """
    Parse and interpret raw CLI output into human-readable format.

    This tool takes raw network device output and returns it in a format
    that's ready to be presented to the user.

    Use this tool IMMEDIATELY after run_network_command returns output.

    Args:
        cli_output: Raw CLI output from network device

    Returns:
        Formatted, human-readable interpretation of the output
    """
    if not cli_output or cli_output.strip() == "":
        return "No output received from the device."

    # Return the output with a clear header for the LLM to interpret
    return f"""Network Device Output:
{"=" * 60}
{cli_output}
{"=" * 60}

Please provide a clear, human-friendly summary of the above output."""
