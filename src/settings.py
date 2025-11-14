"""Settings and configuration management."""


class Settings:
    """Manage AI agent settings."""

    MODEL_OPTIONS = {
        '1': (
            'openai/gpt-oss-120b',
            'GPT-OSS 120B (Recommended - Best for networking)',
        ),
        '2': ('llama-3.3-70b-versatile', 'Llama 3.3 70B (High quality)'),
        '3': ('llama-3.1-8b-instant', 'Llama 3.1 8B (Fast & economical)'),
    }

    TEMPERATURE_OPTIONS = {
        '1': (0.0, 'Focused (Deterministic)'),
        '2': (0.1, 'Balanced (Recommended)'),
        '3': (0.3, 'Creative (More varied)'),
    }

    PLATFORM_OPTIONS = {
        '1': ('cisco_ios', 'Cisco IOS'),
        '2': ('cisco_nxos', 'Cisco NX-OS'),
        '3': ('cisco_xr', 'Cisco IOS-XR'),
    }

    def __init__(self):
        """Initialize settings with defaults."""
        self.model_name = 'openai/gpt-oss-120b'
        self.temperature = 0.1
        self.verbose = False
        self.timeout = 60
        self.platform = 'cisco_ios'

    @staticmethod
    def get_model() -> tuple:
        """Prompt user to select AI model."""
        print("\n🤖 AI Model Selection:")
        for key, (_, description) in Settings.MODEL_OPTIONS.items():
            print(f"   {key}. {description}")

        choice = input("   Select model [1]: ").strip() or '1'
        model, _ = Settings.MODEL_OPTIONS.get(choice, Settings.MODEL_OPTIONS['1'])
        return model

    @staticmethod
    def get_temperature() -> float:
        """Prompt user to select response temperature."""
        print("\n🎯 Response Style:")
        for key, (_, description) in Settings.TEMPERATURE_OPTIONS.items():
            print(f"   {key}. {description}")

        choice = input("   Select style [2]: ").strip() or '2'
        temp, _ = Settings.TEMPERATURE_OPTIONS.get(
            choice, Settings.TEMPERATURE_OPTIONS['2']
        )
        return temp

    @staticmethod
    def get_platform() -> str:
        """Prompt user to select device platform."""
        print("\n🔌 Device Platform:")
        for key, (_, description) in Settings.PLATFORM_OPTIONS.items():
            print(f"   {key}. {description}")

        choice = input("   Select platform [1]: ").strip() or '1'
        platform, _ = Settings.PLATFORM_OPTIONS.get(
            choice, Settings.PLATFORM_OPTIONS['1']
        )
        return platform

    @staticmethod
    def get_verbose() -> bool:
        """Prompt user for verbose mode."""
        verbose_input = input("\n📝 Enable verbose mode? (y/n) [n]: ").strip().lower()
        return verbose_input in ['y', 'yes']

    @staticmethod
    def get_timeout() -> int:
        """Prompt user for API timeout."""
        timeout_input = input("\n⏱️  API timeout in seconds [60]: ").strip()
        return int(timeout_input) if timeout_input.isdigit() else 60

    @staticmethod
    def prompt_all() -> dict:
        """Prompt user for all settings."""
        print("\n" + "=" * 60)
        print("AI Network Agent - Configuration")
        print("=" * 60)

        return {
            'model_name': Settings.get_model(),
            'temperature': Settings.get_temperature(),
            'platform': Settings.get_platform(),
            'verbose': Settings.get_verbose(),
            'timeout': Settings.get_timeout(),
        }
