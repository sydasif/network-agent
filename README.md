# AI Network Agent - Natural Language Network Automation

Talk to your network devices using natural language! An AI-powered agent that understands your questions, executes the right commands, and provides intelligent summaries.

## 🎯 What It Does

Instead of manually running commands and parsing outputs, simply ask:

```text
💬 "Show me all interfaces and their status"
💬 "What's the device uptime?"
💬 "Which interfaces have errors?"
```

The AI agent will:

1. Understand your question
2. Decide which commands to run
3. Execute them on your device
4. Analyze and summarize the results
5. Give you a clear, concise answer

## ✨ Key Features

- **Natural Language Interface** — Ask questions in plain English
- **Intelligent Command Execution** — AI decides which commands to run
- **Automated Analysis** — Parses and summarizes device output
- **Modular Architecture** — Clean, maintainable code structure
- **Easy Setup** — Works with Cisco devices via SSH
- **Free AI** — Uses Groq's free Llama inference

## 📋 Prerequisites

- Python 3.12+
- `uv` package manager (optional but recommended)
- Groq API key (free at <https://console.groq.com/keys>)
- Network device with SSH access (Cisco IOS)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/sydasif/network-agent.git
cd network-agent
```

### 2. Install Dependencies

```bash
uv sync
# or: pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here
DEVICE_PASSWORD=your_device_password  # Optional
```

### 4. Run

```bash
uv run main.py
```

## 📁 Project Structure

```bash
network-agent/
├── main.py                 # Entry point
├── src/                    # Application modules
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── network_device.py  # Device connection
│   ├── agent.py           # AI agent setup
│   ├── interface.py       # User interface
│   └── utils.py           # Utilities
├── pyproject.toml         # Project dependencies
├── .env                   # Environment secrets
└── README.md              # This file
```

## 🏗️ Architecture

### Modules

| Module | Class | Responsibility |
|--------|-------|-----------------|
| `config.py` | `ConfigManager` | Load environment variables and credentials |
| `network_device.py` | `DeviceConnection` | SSH connection and command execution |
| `agent.py` | `Agent` | LLM setup and AI reasoning |
| `interface.py` | `UserInterface` | Interactive CLI interface |
| `utils.py` | — | Formatting and utility functions |

### Data Flow

```text
User Input
    ↓
UserInterface (src/interface.py)
    ├─ Prompts for device credentials
    ├─ Gets Groq API key
    └─ Runs interactive session
        ↓
    Agent (src/agent.py)
    ├─ Receives user question
    ├─ LLM thinks about which commands to run
    └─ Executes via DeviceConnection
        ↓
    DeviceConnection (src/network_device.py)
    └─ Connects via Netmiko SSH
        ↓
    Network Device (Cisco Router/Switch)
    └─ Returns command output
        ↓
    Agent (analyzes output)
    └─ LLM generates human-readable response
        ↓
    UserInterface (displays result)
```

## 💬 Example Usage

```bash
$ uv run main.py

============================================================
AI Network Agent
============================================================

Device IP: 192.168.1.1
Username: admin
Password: ****
✓ Connected to 192.168.1.1

============================================================
Ready! Type 'quit' to exit
============================================================

💬 Ask: Show me all interfaces

------------------------------------------------------------
I found 4 interfaces on your device:

1. **GigabitEthernet0/0** - UP (192.168.1.1)
2. **GigabitEthernet0/1** - UP (10.1.0.1)
3. **GigabitEthernet0/2** - DOWN
4. **Loopback0** - UP (10.0.0.1)
------------------------------------------------------------

💬 Ask: What's the device uptime?

------------------------------------------------------------
The device has been running for:
- 2 days
- 4 hours
- 30 minutes
------------------------------------------------------------

💬 Ask: quit
✓ Disconnected
```

## 🎓 Example Queries

### Device Information

- "What version is running?"
- "What's the hostname?"
- "Show me the uptime"
- "What's the serial number?"

### Interface Management

- "List all interfaces"
- "Which interfaces are down?"
- "Show me interface errors"
- "What's the status of GigabitEthernet0/1?"
- "Show me interface bandwidth utilization"

### Routing

- "Show me the routing table"
- "What's the default gateway?"
- "Show me all static routes"
- "Are there any BGP neighbors?"

### Troubleshooting

- "Are there any errors in the logs?"
- "Show me interface errors"
- "Is there any packet loss?"
- "Show me devices with high CPU"

## 🔧 Technical Stack

### Core Dependencies

- **Netmiko** (4.6.0+) — SSH device connection and command execution
- **LangChain** (0.1+) — AI framework and agent orchestration
- **LangGraph** (1.0+) — Agent state management
- **Groq** (0.33+) — LLM API client
- **python-dotenv** (1.2+) — Environment variable management

### Models

- **Llama 3.3-70B** (via Groq) — Fast, free LLM inference

### Python Version

- Python 3.12+ (uses modern type hints and syntax)

## 🔒 Security Considerations

⚠️ **Important Security Practices:**

1. **Never hardcode credentials** — Always use `.env` file
2. **Protect `.env` file** — Add to `.gitignore` (never commit)
3. **Use SSH keys** — When possible, instead of passwords
4. **Limit API access** — Use Groq API keys with minimal permissions
5. **Read-only mode** — This setup only runs `show` commands
6. **Secure network** — Run from a secure management network
7. **Audit trail** — Consider logging all interactions
8. **Access control** — Restrict who can run this tool

### Example `.gitignore`

```bash
.env
.venv/
__pycache__/
*.pyc
.DS_Store
```

## ⚠️ Troubleshooting

### Connection Timeout

```bash
Error: Connection timeout
```

**Solution:**

- Verify device IP address: `ping 192.168.1.1`
- Check SSH is enabled on device
- Verify firewall allows SSH (port 22)
- Test SSH manually: `ssh admin@192.168.1.1`

### Authentication Failed

```bash
Error: Authentication failed
```

**Solution:**

- Verify username and password are correct
- Check user has SSH access privilege
- Ensure `.env` file has correct credentials
- Try SSH manually first to debug

### API Rate Limit

```bash
Error: Rate limit exceeded
```

**Solution:**

- Groq free tier: 30 requests/minute
- Wait between queries
- Consider upgrading to paid tier for production use

### Command Not Recognized

```bash
Error: Invalid command
```

**Solution:**

- Verify device OS (IOS vs NX-OS commands differ)
- Try command manually on device first
- Check device capabilities
- Some devices need privilege level

## 📈 Next Steps & Enhancements

Potential improvements:

- [ ] Support multiple device types (NX-OS, IOS-XR, ASA)
- [ ] Configuration change capabilities
- [ ] Multi-device management and queries
- [ ] Web UI dashboard
- [ ] Scheduled automated health checks
- [ ] Alert notifications and reporting
- [ ] Command history and logging
- [ ] Custom system prompts per device type
- [ ] Parallel device queries
- [ ] Integration with monitoring systems

## 🤝 Contributing

This is a modular, extensible codebase. Contributions welcome for:

- Adding support for more device types
- Improving LLM prompts and accuracy
- Adding new tools and capabilities
- Enhanced error handling
- Performance optimizations
- Documentation improvements

## 💡 How It Works

### The Agent Flow

1. **Understanding** — LLM interprets user's natural language question
2. **Planning** — LLM decides which network commands to execute
3. **Execution** — Netmiko runs commands on the device via SSH
4. **Analysis** — LLM analyzes raw command output
5. **Response** — LLM generates a clear, human-readable answer

### Example Flow

```text
User: "Which interfaces have errors?"
  ↓
Agent: "I should run 'show interfaces' and 'show interfaces status'"
  ↓
Execution: SSH runs both commands
  ↓
Output: Raw Cisco CLI output
  ↓
Analysis: LLM parses for error counts
  ↓
Response: "Interface Gi0/1 has 15 input errors and 2 output errors"
```

## 🚀 Performance

- **Response Time**: 2-5 seconds (including SSH + LLM inference)
- **Groq Latency**: ~500ms for free tier
- **SSH Connection**: ~1 second
- **Command Execution**: ~1-2 seconds typical

## 📜 License

MIT License - See LICENSE file for details

## 🆘 Getting Help

1. **Start Simple** — Test with basic `show` commands first
2. **Debug SSH** — Verify you can SSH manually before using agent
3. **Check Credentials** — Ensure `.env` has correct API key and device password
4. **Review Logs** — Error messages indicate what went wrong
5. **Refer to blog.md** — Detailed explanation of architecture

## 🎯 Use Cases

- **Network Troubleshooting** — Quick diagnostics without CLI hunting
- **Health Checks** — Regular device status verification
- **Training** — Learn networking concepts interactively
- **Automation** — Integrate into larger automation workflows
- **Documentation** — AI-generated device reports

## ✅ What's Supported

- ✅ Cisco IOS devices (routers and switches)
- ✅ SSH connections with username/password
- ✅ Show commands (read-only)
- ✅ Natural language queries
- ✅ Command output analysis and summarization
- ✅ Error handling and user feedback

## ❌ What's Not Supported

- ❌ Configuration changes (by design - safety first)
- ❌ Non-Cisco devices (yet)
- ❌ Telnet connections (SSH only)
- ❌ Public key authentication (username/password for now)

---

**Happy Automating!** 🚀🤖
