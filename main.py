"""
AI Agent for Network Devices - Inventory Edition
Talk to multiple network devices using natural language!
"""

from src.interface import UserInterface


def main():
    """Main entry point."""
    user_interface = UserInterface()
    user_interface.run()


if __name__ == "__main__":
    main()
