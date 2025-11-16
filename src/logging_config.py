import logging
import sys


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""

    # Root logger
    root_logger = logging.getLogger("net_agent")
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Clear existing handlers to prevent duplicate logs in case of re-configuration
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Formatter (no colors in logs, colors only in console via separate mechanism)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    return root_logger


# Specialized loggers
def get_verbose_logger():
    return logging.getLogger("net_agent.verbose")


def get_audit_logger():
    return logging.getLogger("net_agent.audit")
