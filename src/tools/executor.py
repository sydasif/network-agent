from langchain_core.tools import tool

from src.core.command_executor import CommandExecutor
from src.core.device_manager import DeviceManager
from src.core.device_router import DeviceRouter
from src.core.inventory import InventoryManager
from src.core.sensitive_data import SensitiveDataHandler
from src.core.validation import ValidationPipeline


# Load core components
inventory = InventoryManager("inventory.yaml")
device_manager = DeviceManager()
router = DeviceRouter(device_manager, inventory)
validator = ValidationPipeline()
executor = CommandExecutor()
sanitizer = SensitiveDataHandler()


@tool
def run_network_command(query: str) -> str:
    """
    Execute network CLI commands on devices.

    Use this tool when the user wants to:
    - Run show commands (show vlan, show interfaces, show version, etc.)
    - Get device configuration or status
    - Execute any CLI command on a network device

    Input should be the user's query including device name and command.
    Example inputs: "show vlans on D1", "check interfaces on D2"

    Returns: Raw CLI output from the device
    """

    # 1 — Extract device reference from query
    device_name, cleaned_query = router.extract_device_reference(query)
    if not device_name:
        return "No device mentioned in the query."

    # 2 — Find device in inventory
    device = inventory.find_device_by_name(device_name)
    if not device:
        return f"Device '{device_name}' not found in inventory."

    # 3 — Switch or create new session
    session = device_manager.switch_device_session(device)
    if not session:
        return f"Could not create session for {device.name}."

    # 4 — Validate CLI
    cleaned_query = validator.sanitize_query(cleaned_query)
    validator.validate_query(cleaned_query)

    # 5 — Execute command
    raw_output = executor.execute_command(cleaned_query, session)

    # 6 — Sanitize and return output
    return sanitizer.clean_output(raw_output)
