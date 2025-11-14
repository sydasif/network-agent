"""Special command handling for agent interactions."""

from typing import ClassVar


class Commands:
    """Handle special commands in the interactive session."""

    SPECIAL_COMMANDS: ClassVar[dict[str, str]] = {
        "/cmd": "Execute command directly (bypass AI)",
        "/stats": "Show session statistics",
        "/history": "Show command history",
        "/help": "Show available commands",
        "/quit": "Exit the application",
    }

    @staticmethod
    def is_special_command(query: str) -> bool:
        """Check if query is a special command."""
        return query.strip().startswith("/")

    @staticmethod
    def handle_direct_command(agent, query: str) -> tuple:
        """
        Handle /cmd direct command execution.

        Returns:
            (is_executed, response)
        """
        if not query.strip().startswith("/cmd"):
            return False, None

        command = query.strip()[5:].strip()  # Remove '/cmd '
        if not command:
            return True, "❌ No command specified. Usage: /cmd <command>"

        response = agent.execute_direct_command(command)
        return True, response

    @staticmethod
    def handle_statistics(agent) -> str:
        """Handle /stats command."""
        stats = agent.get_statistics()
        output = "\n📊 Session Statistics:\n"
        output += f"   Total commands: {stats['total_commands']}\n"
        output += f"   Successful: {stats['successful_commands']}\n"
        output += f"   Failed: {stats['failed_commands']}\n"
        output += f"   Rate limit status: {stats['rate_limit_used']}\n"
        output += f"   Rate limit active: {stats['rate_limit_active']}\n"
        output += "\n🤖 Model Information:\n"
        output += f"   Primary model: {stats['primary_model']}\n"
        output += f"   Current model: {stats['current_model']}\n"
        output += f"   Fallbacks used: {stats['model_fallbacks']}\n"
        if stats["model_usage"]:
            output += "   Model usage:\n"
            for model, count in stats["model_usage"].items():
                output += f"      - {model}: {count} requests\n"
        return output

    @staticmethod
    def handle_history(agent, limit: int = 5) -> str:
        """Handle /history command."""
        history = agent.get_history(limit)
        if not history:
            return "\n📜 No command history available."

        output = f"\n📜 Last {len(history)} Commands:\n"
        for i, entry in enumerate(history, 1):
            status = "✅" if entry["success"] else "❌"
            output += (
                f"   {i}. {status} {entry['timestamp']} - {entry['command'][:50]}\n"
            )
        return output

    @staticmethod
    def handle_help() -> str:
        """Handle /help command."""
        output = "\n📚 Available Commands:\n"
        for cmd, description in Commands.SPECIAL_COMMANDS.items():
            output += f"   {cmd:<10} - {description}\n"
        output += "\n💡 Natural Language: "
        output += "Ask questions naturally (AI processes with tools)\n"
        return output

    @staticmethod
    def process_command(agent, query: str) -> tuple:
        """
        Process special commands or indicate not a special command.

        Returns:
            (is_special_command, response)
        """
        if not Commands.is_special_command(query):
            return False, None

        query_lower = query.strip().lower()

        # Direct command execution
        if query_lower.startswith("/cmd"):
            is_executed, response = Commands.handle_direct_command(agent, query)
            return is_executed, response

        # Statistics
        if query_lower.startswith("/stats"):
            return True, Commands.handle_statistics(agent)

        # History
        if query_lower.startswith("/history"):
            # Extract limit if provided: /history 10
            parts = query.split()
            limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
            return True, Commands.handle_history(agent, limit)

        # Help
        if query_lower.startswith("/help"):
            return True, Commands.handle_help()

        # Unknown special command
        return True, (
            f"❌ Unknown command: {query}\nType '/help' for available commands."
        )
