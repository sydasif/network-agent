"""User interface for network automation agent."""

from .agent import Agent
from .commands import Commands
from .config import ConfigManager
from .network_device import DeviceConnection
from .settings import Settings
from .utils import print_formatted_header, print_line_separator


class UserInterface:
    """Interactive user interface for network automation."""

    def __init__(self):
        """Initialize the user interface."""
        self.config_manager = ConfigManager()
        self.device = None
        self.assistant = None

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
        """Run the interactive chat session."""
        print("\n" + "=" * 60)
        print("Ready! Type '/help' for commands or 'quit' to exit")
        print("=" * 60 + "\n")

        while True:
            question = input("\n💬 Ask: ").strip()

            if question.lower() in ["quit", "exit"]:
                break

            if not question:
                continue

            # Check for special commands
            is_special, response = Commands.process_command(self.assistant, question)
            if is_special:
                if response:
                    print_line_separator()
                    print(response)
                    print_line_separator()
                continue

            # Regular question to AI
            print_line_separator()
            answer = self.assistant.answer_question(question)
            print(answer)
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
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.device:
                self.device.disconnect()
