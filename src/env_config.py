"""Environment configuration management."""

import getpass
import os
from dotenv import load_dotenv


class EnvConfigManager:
    """Manage environment variables and secrets."""

    def __init__(self):
        """Initialize configuration by loading environment variables."""
        load_dotenv()

    @staticmethod
    def get_groq_api_key() -> str:
        """Get Groq API key from environment."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Error: Set GROQ_API_KEY in .env file")

        # NEVER log or display the actual API key
        if os.getenv("DEBUG"):
            from .sensitive_data import SensitiveDataProtector
            masked_key = SensitiveDataProtector.mask_api_key(api_key)
            print(f"[DEBUG] Using API key: {masked_key}")

        return api_key

    @staticmethod
    def get_device_password(prompt: bool = True) -> str:
        """Get device password from environment or prompt user."""
        password = os.getenv("DEVICE_PASSWORD")

        if password:
            # Password found in .env file
            return password

        if prompt:
            # Prompt user for password
            return getpass.getpass("Password: ")

        # No password available
        return ""
