"""Parser tool for network output."""

from langchain_core.tools import tool


@tool
def parse_network_output(cli_output: str) -> str:
    """
    Convert raw CLI output into a readable and interpreted answer.
    """
    return f"Here is the interpreted result:\n\n{cli_output}"
