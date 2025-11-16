"""Console UI for network automation - display and formatting only."""

import sys


class Console:
    """Console output abstraction for consistent formatting."""
    
    class Colors:
        PROMPT = "\033[96m"  # Cyan for prompts
        SUCCESS = "\033[92m"  # Green for success
        ERROR = "\033[91m"  # Red for errors
        WARNING = "\033[93m"  # Yellow for warnings
        INFO = "\033[94m"  # Blue for info
        RESET = "\033[0m"

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        if not sys.stdout.isatty():
            return text
        return f"{color}{text}{cls.Colors.RESET}"
    
    @classmethod
    def success(cls, msg: str) -> str:
        return cls.colorize(msg, cls.Colors.SUCCESS)
    
    @classmethod
    def error(cls, msg: str) -> str:
        return cls.colorize(msg, cls.Colors.ERROR)
    
    @classmethod
    def warning(cls, msg: str) -> str:
        return cls.colorize(msg, cls.Colors.WARNING)
    
    @classmethod
    def info(cls, msg: str) -> str:
        return cls.colorize(msg, cls.Colors.INFO)
    
    @classmethod
    def prompt(cls, msg: str) -> str:
        return cls.colorize(msg, cls.Colors.PROMPT)