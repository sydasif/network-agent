"""User interface for network automation agent."""

import re
import time
import getpass
from .agent import Agent
from .audit import AuditLogger, SecurityEventType
from .exceptions import QueryTooLongError, BlockedContentError
from .network_device import DeviceConnection
from .sensitive_data import SensitiveDataProtector
from .settings import settings
from .utils import print_formatted_header, print_line_separator


class InterfaceColors:
    """Colors for user interface elements."""
    PROMPT = '\033[96m'      # Cyan for prompts
    SUCCESS = '\033[92m'     # Green for success
    ERROR = '\033[91m'       # Red for errors
    WARNING = '\033[93m'     # Yellow for warnings
    INFO = '\033[94m'        # Blue for info
    RESET = '\033[0m'


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
            QueryTooLongError: If query exceeds maximum length
            BlockedContentError: If query contains blocked patterns
        """
        # Check if query is empty
        if not query or not query.strip():
            raise BlockedContentError(query, "Empty query")

        # Check length limits (now configurable)
        if len(query) > self.max_query_length:
            error_message = (
                f"❌ Query too long ({len(query)} characters)\n"
                f"   Maximum allowed: {self.max_query_length} characters\n"
                f"   Please shorten your question."
            )

            # Log validation failure to audit system
            if self.audit_logger:
                self.audit_logger.log(SecurityEventType.ERROR, f"Validation failed: Length exceeded. Query: {query[:200]}", severity="warning")

            raise QueryTooLongError(len(query), self.max_query_length)

        # Check for blocked patterns (immediate rejection)
        query_lower = query.lower()
        for pattern in settings.blocked_keywords:
            if re.search(pattern, query_lower, re.IGNORECASE):
                error_message = (
                    f"❌ Query contains blocked content\n"
                    f"   Pattern detected: {pattern}\n"
                    f"   This type of input is not allowed for security reasons."
                )

                # Log validation failure to audit system
                if self.audit_logger:
                    self.audit_logger.log(SecurityEventType.ERROR, f"Validation failed: Blocked pattern: {pattern}. Query: {query[:200]}", severity="critical")

                raise BlockedContentError(query, pattern)

    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize query by removing/escaping dangerous content.

        Args:
            query: Raw user input

        Returns:
            Sanitized query safe for LLM processing
        """
        # Remove null bytes
        query = query.replace('\x00', '')

        # Remove excessive whitespace
        query = ' '.join(query.split())

        # Remove HTML/XML tags
        query = re.sub(r'<[^>]+>', '', query)

        # Escape backticks (prevent code block injection)
        query = query.replace('`', "'")

        # Limit consecutive special characters
        query = re.sub(r'([^Ws])\1{3,}', r'\1\1', query)

        return query.strip()


class UserInterface:
    """Interactive user interface for network automation."""

    def __init__(self):
        """Initialize the user interface."""
        self.device = None
        self.assistant = None
        self.query_count = 0

        self.max_queries_per_session = settings.max_queries_per_session

        self.audit_logger = AuditLogger(
            log_dir=settings.log_directory,
            enable_console=settings.enable_console_logging,
            enable_file=settings.enable_file_logging,
            log_level=settings.log_level,
        )

        self.validator = InputValidator(
            audit_logger=self.audit_logger,
            max_query_length=settings.max_query_length
        )

        self.data_protector = SensitiveDataProtector()

    def _prompt_for_device_credentials(self):
        """Prompt user for device connection details."""
        hostname = input("\nDevice IP: ").strip()
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        return hostname, username, password

    def _setup_network_assistant(self):
        """Initialize the device connection and agent with settings."""
        self.device = DeviceConnection()
        self.assistant = Agent(
            groq_api_key=settings.groq_api_key,
            device=self.device,
            model_name=settings.model_name,
            temperature=settings.temperature,
            verbose=False, # Hardcoded for now
            timeout=settings.api_timeout,
            audit_logger=self.audit_logger,
        )

    def _run_interactive_session(self):
        """Run the interactive chat session with styled output."""
        print("\n" + "=" * 60)
        print("Ready! Type 'quit' to exit")
        print("=" * 60 + "\n")

        while True:
            # Check session limits
            if self.query_count >= self.max_queries_per_session:
                print(
                    f"\n⚠️  Session limit reached ({self.max_queries_per_session} queries)\n"
                    f"   Please restart the application for a new session."
                )
                break

            try:
                # Colored prompt
                question = input(f"\n{InterfaceColors.PROMPT}💬 Ask:{InterfaceColors.RESET} ").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{InterfaceColors.INFO}👋 Interrupted. Exiting...{InterfaceColors.RESET}")
                break

            # Handle exit commands
            if question.lower() in ["quit", "exit", "q"]:
                break

            # Skip empty input
            if not question:
                continue

            # CRITICAL: Validate user input before processing
            try:
                self.validator.validate_query(question)
            except (QueryTooLongError, BlockedContentError) as e:
                print_line_separator()
                print(str(e))
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
                print(f"❌ Error processing query: {e!s}")
                if self.assistant and self.assistant.verbose:
                    import traceback
                    traceback.print_exc()

            print_line_separator()

    def run(self):
        """Run the user interface application."""
        print_formatted_header("AI Network Agent")

        try:
            # Get connection details
            hostname, username, password = self._prompt_for_device_credentials()

            # Initialize assistant with settings
            self._setup_network_assistant()

            # Log session start
            self.audit_logger.log_session_start(
                user=username,
                device=hostname,
                model=settings.model_name,
            )

            # Connect to device
            try:
                self.device.connect(hostname, username, password)
                self.audit_logger.log_connection_established(hostname, username)
            except ConnectionError as e:
                self.audit_logger.log_connection_failed(hostname, username, str(e))
                raise

            # Run interactive session
            self._run_interactive_session()

        except ValueError as e:
            self.audit_logger.log(SecurityEventType.ERROR, f"Configuration error: {e}", severity="error")
            print(f"Error: {e}")
        except ConnectionError as e:
            print(f"{e}")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
        except Exception as e:
            self.audit_logger.log(SecurityEventType.ERROR, f"Unexpected error: {e}", severity="critical")
            print(f"Error: {e}")
            if self.assistant and self.assistant.verbose:
                import traceback
                traceback.print_exc()
        finally:
            if self.device:
                self.device.disconnect()

            self.audit_logger.close()
            print(f"\n📝 Audit logs saved to: {self.audit_logger.log_dir}/audit_{self.audit_logger.session_id}.log")