"""Utility functions and helpers."""


def print_formatted_header(text: str, width: int = 60):
    """Print a formatted header with borders."""
    print("=" * width)
    print(text)
    print("=" * width)


def print_line_separator(width: int = 60):
    """Print a horizontal separator line."""
    print("-" * width)
