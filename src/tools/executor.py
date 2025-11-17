"""Executor tool for network commands."""

from langchain_core.tools import tool

from src.core.command_executor import CommandExecutor
from src.core.device_manager import DeviceManager
from src.core.device_router import DeviceRouter
from src.core.inventory import InventoryManager
from src.core.sensitive_data import SensitiveDataHandler
from src.core.validation import ValidationPipeline


inv = InventoryManager("inventory.yaml")
router = DeviceRouter(DeviceManager(), inv)
validator = ValidationPipeline()
executor = CommandExecutor()
san = SensitiveDataHandler()


@tool
def run_network_command(query: str) -> str:
    """
    Full pipeline:
    extract device → validate → sanitize → execute and return CLI output.
    """
    # extract device
    device, cleaned = router.extract_device_reference(query)

    # validate and clean
    cleaned = validator.sanitize_query(cleaned)
    validator.validate_query(cleaned)

    # switch device and run
    device_session = router.device_manager.switch_device_session(device)
    output = executor.execute_command(cleaned, device_session)

    # sanitize CLI output
    return san.clean_output(output)
