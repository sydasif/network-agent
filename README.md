# Building an AI Agent for Network Automation: Talk to Your Router Like a Human

Imagine asking your router a question in plain English and getting a clear, direct answer. No long CLI outputs, no command hunting, no guesswork. In this guide, you’ll build a Python agent that connects to Cisco devices, runs commands through Netmiko, and replies with AI-generated summaries.

## What We're Building

A Python application where you can type:

- "Show me all interfaces and their status"
- "What's the device uptime?"
- "Are there any errors?"

And the AI will:

1. Figure out which commands to run
2. Execute them on your device
3. Analyze the output
4. Give you a clear answer

## The Magic Behind It

We're combining three powerful tools:

1. **Netmiko** - Connects to network devices via SSH
2. **LangChain** - Framework for building AI applications
3. **Groq** - Fast, free AI inference (using Llama models)

## Prerequisites

Before we start, you'll need:

```bash
# Python 3.12+
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Get a free Groq API key
# Visit: https://console.groq.com/keys
```

## Project Setup

### 1. Create Project Structure

```bash
mkdir network-ai-agent
cd network-ai-agent
```

### 2. Create `pyproject.toml`

```toml
[project]
name = "network-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "groq>=0.33.0",
    "langchain-groq>=1.0.0",
    "langgraph>=1.0.3",
    "netmiko>=4.6.0",
    "python-dotenv>=1.2.1",
]
```

### 3. Create `.env` File

```bash
# Store your secrets here
GROQ_API_KEY=your_groq_api_key_here
DEVICE_PASSWORD=your_device_password  # Optional
```

### 4. Install Dependencies

```bash
uv sync
```

## The Complete Code

Here's the entire application in one file (`main.py`):

```python
"""
AI Agent for Network Devices - Simple Version
Talk to your Cisco router using natural language!
"""

import os
import getpass
from dotenv import load_dotenv
from netmiko import ConnectHandler
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


class NetworkAgent:
    """AI-powered network device assistant."""

    def __init__(self, groq_api_key: str):
        """Initialize the AI agent."""
        # Set up the AI model
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1
        )
        self.connection = None

        # Create a tool the AI can use to run commands
        self.execute_command_tool = tool("execute_show_command")(
            self._execute_command
        )

        # Create the AI agent with the tool
        self.agent = create_react_agent(self.llm, [self.execute_command_tool])

    def connect(self, hostname: str, username: str, password: str):
        """Connect to a network device."""
        device_config = {
            'device_type': 'cisco_ios',
            'host': hostname,
            'username': username,
            'password': password,
            'timeout': 30,
        }
        self.connection = ConnectHandler(**device_config)
        print(f"✓ Connected to {hostname}")

    def disconnect(self):
        """Disconnect from the device."""
        if self.connection:
            self.connection.disconnect()
            print("✓ Disconnected")

    def _execute_command(self, command: str) -> str:
        """Execute a command on the device (used by AI)."""
        if not self.connection:
            return "Error: Not connected to device"

        try:
            output = self.connection.send_command(command)
            return output
        except Exception as e:
            return f"Error: {str(e)}"

    def ask(self, question: str) -> str:
        """Ask the AI a question about the device."""
        # Give the AI instructions
        prompt = f"""You are a network engineer assistant.
Use the execute_show_command tool to run Cisco commands.
Answer the user's question clearly and concisely.

User question: {question}"""

        try:
            result = self.agent.invoke({"messages": [("user", prompt)]})

            # Extract the AI's response
            last_message = result["messages"][-1]
            return last_message.content
        except Exception as e:
            return f"Error: {str(e)}"


def main():
    """Main program."""
    load_dotenv()

    print("="*60)
    print("AI Network Agent")
    print("="*60)

    # Get connection details
    hostname = input("\nDevice IP: ").strip()
    username = input("Username: ").strip()
    password = os.getenv('DEVICE_PASSWORD') or getpass.getpass("Password: ")

    # Get API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("Error: Set GROQ_API_KEY in .env file")
        return

    # Create and connect agent
    agent = NetworkAgent(api_key)

    try:
        agent.connect(hostname, username, password)

        print("\n" + "="*60)
        print("Ready! Type 'quit' to exit")
        print("="*60 + "\n")

        # Chat loop
        while True:
            question = input("\n💬 Ask: ").strip()

            if question.lower() in ['quit', 'exit']:
                break

            if not question:
                continue

            print("\n" + "-"*60)
            answer = agent.ask(question)
            print(answer)
            print("-"*60)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        agent.disconnect()


if __name__ == "__main__":
    main()
```

## How It Works

### 1. **The NetworkAgent Class**

This is the heart of our application. It:

- Connects to the AI (Groq/LangChain)
- Connects to the network device (Netmiko)
- Creates a "tool" the AI can use

### 2. **The Tool System**

The most important part:

```python
self.execute_command_tool = tool("execute_show_command")(
    self._execute_command
)
```

This tells the AI: "Hey, you have a tool called `execute_show_command` that can run commands on a network device!"

### 3. **The Agent**

```python
self.agent = create_react_agent(self.llm, [self.execute_command_tool])
```

This creates an AI agent that can:

- Think about what commands to run
- Use the tool to execute them
- Analyze the results
- Give you an answer

### 4. **The Flow**

```ruby
User: "Show me all interfaces"
  ↓
AI thinks: "I need to run 'show ip interface brief'"
  ↓
AI uses tool: execute_show_command("show ip interface brief")
  ↓
Tool runs command on device via SSH
  ↓
AI analyzes output
  ↓
AI responds: "Here are your interfaces: ..."
```

## Running Your Agent

```bash
# Start the agent
uv run main.py

# Example session:
Device IP: 192.168.1.1
Username: admin
Password: ****
✓ Connected to 192.168.1.1

Ready! Type 'quit' to exit
====================================

💬 Ask: Show me all interfaces, make summary.

------------------------------------
I found 4 interfaces on your device:
1. GigabitEthernet0/0 - UP (192.168.1.1)
2. GigabitEthernet0/1 - UP (10.1.0.1)
3. GigabitEthernet0/2 - DOWN
4. Loopback0 - UP (10.0.0.1)
------------------------------------

💬 Ask: What's the uptime?

------------------------------------
The device has been running for 2 days, 4 hours, 30 minutes.
------------------------------------

💬 Ask: quit
✓ Disconnected
```

## Real-World Example Queries

Here are questions you can ask:

**Basic Info:**

- "What version is running?"
- "What's the hostname?"
- "Show me the uptime"

**Interface Management:**

- "List all interfaces"
- "Which interfaces are down?"
- "Show me interface errors"
- "What's the status of GigabitEthernet0/1?"

**Routing:**

- "Show me the routing table"
- "What's the default gateway?"
- "Show me all static routes"

**Troubleshooting:**

- "Are there any errors in the logs?"
- "Show me interface errors"
- "Is there any packet loss?"

## Why This Is Powerful

### Before (Traditional Way)

```terminal
You: *types* show ip interface brief
Device: *returns 50 lines of output*
You: *manually reads through output*
You: *remembers another command to check*
You: *types* show interfaces status
Device: *returns more output*
You: *correlates information in your head*
```

### After (AI Agent Way)

```terminal
You: "Which interfaces have errors?"
AI: *runs multiple commands automatically*
AI: *analyzes all output*
AI: "Interface GigabitEthernet0/2 has 45 input errors"
```

## Security Notes

🔒 **Important Security Practices:**

1. **Never hardcode passwords** - Always use environment variables
2. **Use SSH keys** when possible
3. **Limit API access** - Store API keys securely
4. **Read-only commands** - This example only runs `show` commands
5. **Network access** - Run from a secure management network

## Troubleshooting

### "Connection timeout"

- Check device IP and SSH access
- Verify firewall rules
- Ensure device allows SSH

### "Authentication failed"

- Verify username/password
- Check privilege level (may need `enable` password)

### "API rate limit"

- Groq free tier: 30 requests/minute
- Wait a moment between queries
- Consider paid tier for production

### "Command not recognized"

- Some commands differ by platform (IOS vs NX-OS)
- Try the direct command: `show vlan brief`
- Check device capabilities

## Next Steps

Want to enhance this? Here are ideas:

1. **Add more platforms**: NX-OS, IOS-XR, ASA
2. **Configuration changes**: Add tools for config commands
3. **Multiple devices**: Connect to many devices at once
4. **Web interface**: Build a web UI
5. **Scheduled queries**: Run automated health checks
6. **Alerting**: Send notifications for issues

## The Complete Picture

Here's what makes this special:

```text
┌─────────────┐
│    You      │
│   (Human)   │
└──────┬──────┘
       │ "Show me interfaces"
       ↓
┌─────────────┐
│  AI Agent   │ ← Thinks & Plans
│  (Llama)    │
└──────┬──────┘
       │ Uses tool: execute_show_command()
       ↓
┌─────────────┐
│  Netmiko    │ ← Connects via SSH
│  (Python)   │
└──────┬──────┘
       │ Runs command
       ↓
┌─────────────┐
│   Router    │
│  (Cisco)    │
└─────────────┘
```

## Conclusion

In just **100 lines of Python**, we've built an AI agent that:

- Understands natural language
- Executes network commands
- Analyzes device output
- Responds intelligently

This is the power of combining AI with network automation. No more memorizing commands, no more parsing lengthy outputs - just ask questions and get answers!

## Try It Yourself

1. Get a Groq API key (free): <https://console.groq.com>
2. Copy the code above
3. Set up your `.env` file
4. Run `uv sync && uv run main.py`
5. Start chatting with your network devices!

---

**Questions or improvements?** This is a starting point - customize it for your network environment and use cases!

Happy automating! 🚀🤖
