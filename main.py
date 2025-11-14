"""
AI Agent for Network Devices - Modular Version
Talk to your network device using natural language!
"""

from src.interface import UserInterface


def main():
    """Main entry point."""
    user_interface = UserInterface()
    user_interface.run()


if __name__ == "__main__":
    main()
