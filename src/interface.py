"""User interface for network automation agent."""

import re
from .agent import Agent
from .commands import Commands
from .config import ConfigManager
from .network_device import DeviceConnection
from .settings import Settings
from .utils import print_formatted_header, print_line_separator


class InputValidator:
    """Validate and sanitize user input."""
    
    # Maximum input length (characters)
    MAX_QUERY_LENGTH = 500
    
    # Suspicious patterns that might indicate prompt injection
    SUSPICIOUS_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"new\s+instructions",
        r"system\s*:?\s*you\s+are",
        r"override\s+security",
        r"bypass\s+validation",
        r"execute\s+command",
        r"run\s+command",
        r"<!--.*?-->",  # HTML comments
        r"```.*?```",   # Code blocks
        r"###\s*new",   # Markdown headers suggesting override
        r"reload",      # Direct mention of dangerous commands
        r"write\s+erase",
        r"configure\s+terminal",
        r"conf\s+t",
        r"copy\s+running",
        r"no\s+",       # Configuration removal
    ]
    
    # Patterns that are always blocked
    BLOCKED_PATTERNS = [
        r"<script",     # Script injection
        r"javascript:",  # JavaScript injection
        r"\x00",        # Null bytes
        r"\.\.\/",      # Path traversal
        r"base64",      # Encoded commands
        r"eval\(",      # Code execution
    ]
    
    @staticmethod
    def validate_query(query: str) -> tuple[bool, str]:
        """Validate user query for security concerns.
        
        Args:
            query: User input query
            
        Returns:
            Tuple of (is_valid, error_message)
            If valid: (True, "")
            If invalid: (False, "error message")
        """
        # Check if query is empty
        if not query or not query.strip():
            return False, "Empty query"
        
        # Check length limits
        if len(query) > InputValidator.MAX_QUERY_LENGTH:
            return False, (
                f"❌ Query too long ({len(query)} characters)\n"
                f"   Maximum allowed: {InputValidator.MAX_QUERY_LENGTH} characters\n"
                f"   Please shorten your question."
            )
        
        # Check for blocked patterns (immediate rejection)
        query_lower = query.lower()
        for pattern in InputValidator.BLOCKED_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return False, (
                    f"❌ Query contains blocked content\n"
                    f"   Pattern detected: {pattern}\n"
                    f"   This type of input is not allowed for security reasons."
                )
        
        # Check for suspicious patterns (warning + rejection)
        suspicious_matches = []
        for pattern in InputValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                suspicious_matches.append(pattern)
        
        if suspicious_matches:
            return False, (
                f"⚠️  Query contains suspicious patterns\n"
                f"   Detected: {', '.join(suspicious_matches[:3])}\n"
                f"   This looks like a prompt injection attempt.\n"
                f"   Please rephrase your question normally."
            )
        
        # Check for excessive special characters (might be obfuscation)
        special_char_count = sum(1 for c in query if not c.isalnum() and not c.isspace())
        if special_char_count > len(query) * 0.3:  # More than 30% special chars
            return False, (
                f"⚠️  Query contains too many special characters\n"
                f"   This might be an attempt to obfuscate malicious input.\n"
                f"   Please use plain language."
            )
        
        return True, ""
    
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
        self.config_manager = ConfigManager()
        self.device = None
        self.assistant = None
        self.validator = InputValidator()
        self.query_count = 0
        self.max_queries_per_session = 100  # Prevent infinite loops

    def _prompt_for_device_credentials(self):
        """Prompt user for device connection details."""
        hostname = input("\nDevice IP: ").strip()
        username = input("Username: ").strip()
        password = self.config_manager.get_device_password()
        return hostname, username, password

    def _setup_network_assistant(self, api_key: str, settings: dict):
        """Initialize the device connection and agent with settings."""
        self.device = DeviceConnection()
        self.assistant = Agent(
            api_key,
            self.device,
            model_name=settings["model_name"],
            temperature=settings["temperature"],
            verbose=settings["verbose"],
            timeout=settings["timeout"],
        )

    def _run_interactive_session(self):
        """Run the interactive chat session with input validation."""
        print("\n" + "=" * 60)
        print("Ready! Type '/help' for commands or 'quit' to exit")
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
                question = input("\n💬 Ask: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 Interrupted. Exiting...")
                break

            # Handle exit commands
            if question.lower() in ["quit", "exit", "q"]:
                break

            # Skip empty input
            if not question:
                continue

            # Check for special commands (these bypass validation)
            is_special, response = Commands.process_command(self.assistant, question)
            if is_special:
                if response:
                    print_line_separator()
                    print(response)
                    print_line_separator()
                continue

            # CRITICAL: Validate user input before processing
            is_valid, error_message = self.validator.validate_query(question)
            if not is_valid:
                print_line_separator()
                print(error_message)
                print_line_separator()
                continue

            # Sanitize the query
            sanitized_question = self.validator.sanitize_query(question)

            # Log if sanitization changed the query
            if sanitized_question != question and self.assistant.verbose:
                print(f"[SANITIZED] Original: {question}")
                print(f"[SANITIZED] Cleaned:  {sanitized_question}")

            # Increment query counter
            self.query_count += 1

            # Process the validated and sanitized query
            print_line_separator()
            try:
                answer = self.assistant.answer_question(sanitized_question)
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
            # Get configuration settings from user
            settings = Settings.prompt_all()

            # Get connection details
            hostname, username, password = self._prompt_for_device_credentials()

            # Get API key
            api_key = self.config_manager.get_groq_api_key()

            # Initialize assistant with settings
            self._setup_network_assistant(api_key, settings)

            # Connect to device
            self.device.connect(hostname, username, password)

            # Run interactive session
            self._run_interactive_session()

        except ValueError as e:
            print(f"Error: {e}")
        except ConnectionError as e:
            print(f"{e}")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
        except Exception as e:
            print(f"Error: {e}")
            if self.assistant and self.assistant.verbose:
                import traceback
                traceback.print_exc()
        finally:
            if self.device:
                self.device.disconnect()