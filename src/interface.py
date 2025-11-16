"""Simplified user interface for network automation agent with multi-device support."""

import logging
import os
import re
from pathlib import Path

from .simple_agent import SimpleAgent
from .devices import Registry
from .audit import AuditLogger, SecurityEventType
from .exceptions import BlockedContentError, QueryTooLongError
from .logging_config import setup_logging
from .sensitive_data import SensitiveDataProtector
from .settings import settings
from .utils import print_formatted_header, print_line_separator
from .session_manager import SessionManager
from .command_handler import CommandHandler
from .console import Console


logger = logging.getLogger("net_agent.interface")


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
    """Interactive user interface with simplified responsibilities."""

    def __init__(self, inventory_file: str = "inventory.yaml"):
        """Initialize the user interface.

        Args:
            inventory_file: Path to inventory file (YAML or JSON)
        """
        setup_logging(verbose=settings.verbose)
        self.inventory_file = inventory_file
        self.query_count = 0

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

        # Initialize components
        self.device_registry = None
        self.session_manager = SessionManager(self.audit_logger)
        self.command_handler = None
        self.agent = None

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
            Console.info(
                f"📦 Created sample inventory file: {self.inventory_file}\n"
                f"💡 Edit this file to add your network devices.\n",
            )
        )

    def _setup_with_inventory(self):
        """Initialize the system with inventory."""
        # Load inventory
        inventory_path = Path(self.inventory_file)
        if not inventory_path.exists():
            print(
                Console.warning(
                    f"⚠️  Inventory file not found: {self.inventory_file}",
                )
            )
            # Create sample inventory
            self._create_sample_inventory()

        self.device_registry = Registry(str(inventory_path))
        self.command_handler = CommandHandler(self.device_registry)

        self.agent = SimpleAgent(
            groq_api_key=settings.groq_api_key,
            model_name=settings.model_name,
            temperature=settings.temperature,
            verbose=settings.verbose,
            timeout=settings.api_timeout,
            audit_logger=self.audit_logger,
        )

        print(
            Console.success(
                f"📦 Inventory: {len(self.device_registry)} devices loaded",
            )
        )

    def _run_interactive_session(self):
        """Run the interactive chat session with styled output."""
        print("\n💡 Tip: Ask naturally like 'show vlans on SW1' or 'check RTR1 uptime'")
        print("=" * 60)
        print("Ready! Ask questions about any device in your inventory")
        print("Type 'help' for commands or ask naturally")
        print("=" * 60)

        while True:
            # Check session limits
            if self.session_manager.is_session_limit_reached():
                logger.warning(
                    Console.warning(
                        f"\nSession limit reached ({settings.max_queries_per_session} queries)\n"
                        f"   Please restart the application for a new session.",
                    )
                )
                break

            # Get current device for prompt
            current_device = self.device_registry.get_current_name()
            prompt_prefix = f"[{current_device}]" if current_device else ""

            try:
                # Colored prompt
                question = input(
                    f"\n{prompt_prefix}{Console.prompt(' 💬 Ask:')} "
                ).strip()
            except (KeyboardInterrupt, EOFError):
                logger.info(
                    Console.info("\n\n👋 Interrupted. Exiting...")
                )
                break

            # Handle exit commands
            if question.lower() in ["quit", "exit", "q"]:
                break

            # Skip empty input
            if not question:
                continue

            # Handle special commands first
            is_special, response = self.command_handler.handle_special_command(question)
            if is_special:
                print_line_separator()
                print(response)
                print_line_separator()
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
            self.session_manager.increment_query_count()

            # Process the validated and sanitized query
            print_line_separator()

            try:
                answer = self.agent.answer_question(sanitized_question)
                print()
                print(answer)

            except Exception as e:
                logger.error(
                    Console.error(f"❌ Error processing query: {e!s}")
                )
                if self.agent and self.agent.verbose:
                    import traceback

                    traceback.print_exc()

            print_line_separator()

    def run(self):
        """Run the user interface application."""
        print_formatted_header("AI Network Agent - Inventory Edition")

        try:
            # Initialize with inventory
            self._setup_with_inventory()

            # Start session
            self.session_manager.start_session()

            # Run interactive session
            self._run_interactive_session()

        except ValueError as e:
            self.audit_logger.log(
                SecurityEventType.ERROR, f"Configuration error: {e}", severity="error"
            )
            logger.error(Console.error(f"Error: {e}"))
        except Exception as e:
            self.audit_logger.log(
                SecurityEventType.ERROR, f"Unexpected error: {e}", severity="critical"
            )
            logger.error(Console.error(f"Error: {e}"))
            if self.agent and self.agent.verbose:
                import traceback

                traceback.print_exc()
        finally:
            if self.device_registry:
                self.device_registry.disconnect_all()

            self.session_manager.end_session()
            self.audit_logger.close()
            logger.info(
                Console.info(
                    f"\n📝 Audit logs saved to: {self.audit_logger.log_dir}/audit_{self.audit_logger.session_id}.log",
                )
            )
