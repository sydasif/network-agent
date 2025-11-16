"""User interface for network automation agent with multi-device support."""

import logging
import os
import re
import sys
from pathlib import Path

from .agent import EnhancedAgent
from .audit import AuditLogger, SecurityEventType
from .device_manager import DeviceManager
from .exceptions import BlockedContentError, QueryTooLongError
from .inventory import InventoryManager
from .logging_config import setup_logging
from .sensitive_data import SensitiveDataProtector
from .settings import settings
from .utils import print_formatted_header, print_line_separator


logger = logging.getLogger("net_agent.interface")


class ConsoleColors:
    """Console colors for user-facing messages only."""

    PROMPT = "\033[96m"  # Cyan for prompts
    SUCCESS = "\033[92m"  # Green for success
    ERROR = "\033[91m"  # Red for errors
    WARNING = "\033[93m"  # Yellow for warnings
    INFO = "\033[94m"  # Blue for info
    RESET = "\033[0m"

    @staticmethod
    def colorize(text: str, color: str) -> str:
        if not sys.stdout.isatty():
            return text
        return f"{color}{text}{ConsoleColors.RESET}"


class InputValidator:
    """Validate and sanitize user input."""

    def __init__(self, audit_logger=None, max_query_length: int = 500):
        """Initialize the validator.

        Args:
            audit_logger: Optional audit logger for logging validation events
            max_query_length: Maximum allowed query length
        """
        self.audit_logger = audit_logger
        self.max_query_length = max_query_length

    def validate_query(self, query: str) -> None:
        """Validate user query for security concerns.

        Args:
            query: User input query

        Raises:
            QueryTooLongError: If query exceeds length limits
            BlockedContentError: If query contains blocked content
        """
        # Check if query is empty
        if not query or not query.strip():
            if self.audit_logger:
                self.audit_logger.log(
                    SecurityEventType.ERROR,
                    f"Validation failed: Empty query. Query: {query[:200]}",
                    severity="warning",
                )
            raise BlockedContentError(query, "empty")

        # Check length limits (now configurable)
        if len(query) > self.max_query_length:
            # Log validation failure to audit system
            if self.audit_logger:
                self.audit_logger.log(
                    SecurityEventType.ERROR,
                    f"Validation failed: Length exceeded. Query: {query[:200]}",
                    severity="warning",
                )

            raise QueryTooLongError(length=len(query), max_length=self.max_query_length)

        # Check for blocked patterns (immediate rejection)
        query_lower = query.lower()
        for pattern in settings.blocked_keywords:
            if re.search(pattern, query_lower, re.IGNORECASE):
                # Log validation failure to audit system
                if self.audit_logger:
                    self.audit_logger.log(
                        SecurityEventType.ERROR,
                        f"Validation failed: Blocked pattern: {pattern}. Query: {query[:200]}",
                        severity="critical",
                    )

                raise BlockedContentError(content=query, pattern=pattern)

    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize query by removing/escaping dangerous content.

        Args:
            query: Raw user input

        Returns:
            Sanitized query safe for LLM processing
        """
        # Remove null bytes
        query = query.replace("\x00", "")

        # Remove excessive whitespace
        query = " ".join(query.split())

        # Remove HTML/XML tags
        query = re.sub(r"<[^>]+>", "", query)

        # Escape backticks (prevent code block injection)
        query = query.replace("`", "'")

        # Limit consecutive special characters
        query = re.sub(r"([^Ws])\1{3,}", r"\1\1", query)

        return query.strip()


class UserInterface:
    """Interactive user interface for network automation with inventory support."""

    def __init__(self, inventory_file: str = "inventory.yaml"):
        """Initialize the user interface.

        Args:
            inventory_file: Path to inventory file (YAML or JSON)
        """
        setup_logging(verbose=settings.verbose)
        self.device_manager = None
        self.assistant = None
        self.query_count = 0
        self.inventory_file = inventory_file

        self.max_queries_per_session = settings.max_queries_per_session

        self.audit_logger = AuditLogger(
            log_dir=settings.log_directory,
            enable_console=settings.enable_console_logging,
            enable_file=settings.enable_file_logging,
            log_level=settings.log_level,
        )

        self.validator = InputValidator(
            audit_logger=self.audit_logger, max_query_length=settings.max_query_length
        )

        self.data_protector = SensitiveDataProtector()

    def _create_sample_inventory(self):
        """Create a sample inventory file if none exists."""
        if os.path.exists(self.inventory_file):
            return

        sample_content = """# Network Device Inventory
# Format: YAML (you can also use JSON)

devices:
  # Distribution Switches
  - name: S1
    hostname: 192.168.121.101
    username: admin
    password: admin
    device_type: cisco_ios
    description: Floor 1
    location: Building-A-Floor1
    role: distribution

  - name: S2
    hostname: 192.168.121.102
    username: admin
    password: admin
    device_type: cisco_ios
    description: Floor 2
    location: Building-A-Floor2
    role: distribution
"""

        with open(self.inventory_file, "w") as f:
            f.write(sample_content)

        print(
            ConsoleColors.colorize(
                f"📦 Created sample inventory file: {self.inventory_file}\n"
                f"💡 Edit this file to add your network devices.\n",
                ConsoleColors.INFO,
            )
        )

    def _setup_with_inventory(self):
        """Initialize the system with inventory."""
        # Load inventory
        inventory_path = Path(self.inventory_file)
        if not inventory_path.exists():
            print(
                ConsoleColors.colorize(
                    f"⚠️  Inventory file not found: {self.inventory_file}",
                    ConsoleColors.WARNING,
                )
            )
            # Create sample inventory
            self._create_sample_inventory()

        self.inventory_manager = InventoryManager(str(inventory_path))
        self.device_manager = DeviceManager()

        self.assistant = EnhancedAgent(
            groq_api_key=settings.groq_api_key,
            device_manager=self.device_manager,
            inventory_manager=self.inventory_manager,
            model_name=settings.model_name,
            temperature=settings.temperature,
            verbose=settings.verbose,
            timeout=settings.api_timeout,
            audit_logger=self.audit_logger,
        )

        print(
            ConsoleColors.colorize(
                f"📦 Inventory: {len(self.inventory_manager)} devices loaded",
                ConsoleColors.SUCCESS,
            )
        )

    def _handle_special_commands(self, question: str) -> bool:
        """Handle special commands like 'inventory', 'connected', etc.

        Args:
            question: User input question

        Returns:
            True if it was a special command, False otherwise
        """
        command = question.strip().lower()

        if command == "inventory":
            self._show_inventory()
            return True

        if command == "connected":
            self._show_connected_devices()
            return True

        if command.startswith("switch "):
            device_name = command[7:].strip().upper()  # Get device name after "switch "
            self._switch_device(device_name)
            return True

        if command.startswith("disconnect "):
            device_name = (
                command[11:].strip().upper()
            )  # Get device name after "disconnect "
            self._disconnect_device(device_name)
            return True

        if command in ["help", "h"]:
            self._show_help()
            return True

        return False

    def _show_inventory(self):
        """Display the device inventory."""
        print_line_separator()
        print("\n📦 Device Inventory:")
        print()

        # Group devices by role
        roles = {"core": [], "distribution": [], "access": [], "edge": [], "other": []}

        for device in self.inventory_manager.list_devices():
            role = device.role.lower() if device.role else "other"
            if role in roles:
                roles[role].append(device)
            else:
                roles["other"].append(device)

        # Display roles in order
        role_order = ["core", "distribution", "access", "edge", "other"]
        for role in role_order:
            if roles[role]:
                print(f"  {role.upper()}:")
                for device in sorted(roles[role], key=lambda d: d.name):
                    status = (
                        "✓" if self.device_manager.is_connected(device.name) else "○"
                    )
                    print(
                        f"    {status} {device.name:<15} {device.hostname:<15} {device.description or ''}"
                    )
                print()

        if not any(roles.values()):
            print("  No devices in inventory.")
        print_line_separator()

    def _show_connected_devices(self):
        """Display connected devices."""
        print_line_separator()
        print("\n🔌 Connected Devices:")
        print()

        connected_devices = self.device_manager.get_connected_devices()
        current_device = self.device_manager.get_current_device_name()

        if connected_devices:
            for device_name, connection in connected_devices.items():
                status = "✓"
                marker = "  →" if device_name == current_device else "   "
                print(
                    f"{marker} {status} {device_name:<15} {connection.device_config['host']}"
                )
        else:
            print("  No devices currently connected.")
        print_line_separator()

    def _switch_device(self, device_name: str):
        """Switch to a specific device."""
        print_line_separator()
        if device_name not in self.inventory_manager:
            print(f"❌ Device '{device_name}' not found in inventory")
            print(
                f"💡 Available devices: {', '.join(self.inventory_manager.get_device_names())}"
            )
        elif not self.device_manager.is_connected(device_name):
            print(f"❌ Device '{device_name}' is not connected")
        else:
            try:
                self.device_manager.switch_device(device_name)
                print(f"✓ Switched to device: {device_name}")
            except ValueError as e:
                print(f"❌ Could not switch to device '{device_name}': {e}")
        print_line_separator()

    def _disconnect_device(self, device_name: str):
        """Disconnect from a specific device."""
        print_line_separator()
        if not self.device_manager.is_connected(device_name):
            print(f"❌ Device '{device_name}' is not connected")
        else:
            success = self.device_manager.disconnect_from_device(device_name)
            if success:
                print(f"✓ Disconnected from device: {device_name}")
            else:
                print(f"❌ Failed to disconnect from device: {device_name}")
        print_line_separator()

    def _show_help(self):
        """Show help information."""
        print_line_separator()
        print("\n💡 Help - Available Commands:")
        print()
        print("  • Ask naturally: 'show vlans on SW1' or 'check RTR1 uptime'")
        print("  • inventory      - Show all devices in inventory")
        print("  • connected      - Show currently connected devices")
        print("  • switch NAME    - Manually switch to a device (e.g., 'switch RTR1')")
        print("  • disconnect NAME- Disconnect from a device (e.g., 'disconnect SW1')")
        print("  • help           - Show this help")
        print("  • quit           - Exit application")
        print()
        print("  Natural language patterns:")
        print("  • 'show version on RTR1'    - Connect to RTR1 and execute command")
        print("  • 'get interfaces from SW1' - Connect to SW1 and execute command")
        print("  • 'check status at SW2'     - Connect to SW2 and execute command")
        print("  • 'what's the uptime for RTR1' - Connect to RTR1 and execute command")
        print("  • 'show configuration of SW1' - Connect to SW1 and execute command")
        print_line_separator()

    def _run_interactive_session(self):
        """Run the interactive chat session with styled output."""
        print("\n💡 Tip: Ask naturally like 'show vlans on SW1' or 'check RTR1 uptime'")
        print("=" * 60)
        print("Ready! Ask questions about any device in your inventory")
        print("Type 'help' for commands or ask naturally")
        print("=" * 60)

        while True:
            # Check session limits
            if self.query_count >= self.max_queries_per_session:
                logger.warning(
                    ConsoleColors.colorize(
                        f"\nSession limit reached ({self.max_queries_per_session} queries)\n"
                        f"   Please restart the application for a new session.",
                        ConsoleColors.WARNING,
                    )
                )
                break

            # Get current device for prompt
            current_device = self.device_manager.get_current_device_name()
            prompt_prefix = f"[{current_device}]" if current_device else ""

            try:
                # Colored prompt
                question = input(
                    f"\n{prompt_prefix}{ConsoleColors.PROMPT} 💬 Ask:{ConsoleColors.RESET} "
                ).strip()
            except (KeyboardInterrupt, EOFError):
                logger.info(
                    ConsoleColors.colorize(
                        "\n\n👋 Interrupted. Exiting...", ConsoleColors.INFO
                    )
                )
                break

            # Handle exit commands
            if question.lower() in ["quit", "exit", "q"]:
                break

            # Skip empty input
            if not question:
                continue

            # Handle special commands first
            if self._handle_special_commands(question):
                continue

            # CRITICAL: Validate user input before processing
            try:
                self.validator.validate_query(question)
            except (QueryTooLongError, BlockedContentError) as e:
                print_line_separator()
                logger.error(str(e))
                print_line_separator()
                continue

            # Sanitize the query
            sanitized_question = self.validator.sanitize_query(question)

            # Increment query counter
            self.query_count += 1

            # Process the validated and sanitized query
            print_line_separator()

            try:
                answer = self.assistant.answer_question(sanitized_question)
                print()
                print(answer)

            except Exception as e:
                logger.error(
                    ConsoleColors.colorize(
                        f"❌ Error processing query: {e!s}", ConsoleColors.ERROR
                    )
                )
                if self.assistant and self.assistant.verbose:
                    import traceback

                    traceback.print_exc()

            print_line_separator()

    def run(self):
        """Run the user interface application."""
        print_formatted_header("AI Network Agent - Inventory Edition")

        try:
            # Initialize with inventory
            self._setup_with_inventory()

            # Log session start
            self.audit_logger.log_session_start(
                user="network_admin",
                device="inventory_based",
                model=settings.model_name,
            )

            # Run interactive session
            self._run_interactive_session()

        except ValueError as e:
            self.audit_logger.log(
                SecurityEventType.ERROR, f"Configuration error: {e}", severity="error"
            )
            logger.error(ConsoleColors.colorize(f"Error: {e}", ConsoleColors.ERROR))
        except Exception as e:
            self.audit_logger.log(
                SecurityEventType.ERROR, f"Unexpected error: {e}", severity="critical"
            )
            logger.error(ConsoleColors.colorize(f"Error: {e}", ConsoleColors.ERROR))
            if self.assistant and self.assistant.verbose:
                import traceback

                traceback.print_exc()
        finally:
            if self.device_manager:
                self.device_manager.disconnect_all()

            self.audit_logger.close()
            logger.info(
                ConsoleColors.colorize(
                    f"\n📝 Audit logs saved to: {self.audit_logger.log_dir}/audit_{self.audit_logger.session_id}.log",
                    ConsoleColors.INFO,
                )
            )
