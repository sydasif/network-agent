# AI Network Agent - Simplified Network Automation

A streamlined, AI-powered agent that enables natural language interaction with network devices. Built with security and simplicity in mind.

## 🎯 What It Does

Ask questions about your network in plain English:

```text
💬 "Show me all interfaces and their status"
💬 "What's the device uptime?"
💬 "Which interfaces have errors?"
```

The AI agent will understand your question, execute appropriate commands, and provide clear answers.

## ✨ Key Features

- **Natural Language Interface** — Ask questions in plain English
- **Simplified Architecture** — Focus on core functionality without unnecessary complexity
- **Secure by Design** — Built-in command validation and sensitive data protection
- **Easy Setup** — Works with Cisco devices via SSH
- **Free AI** — Uses Groq's free Llama inference

## 📋 Prerequisites

- Python 3.12+
- `uv` package manager (recommended). Install with `pip install uv`.
- Groq API key (free at <https://console.groq.com/keys>)
- Network device with SSH access (Cisco IOS)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-repo/network-agent.git
cd network-agent
```

### 2. Install Dependencies

Create a virtual environment and install the project's dependencies using `uv`.

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install the core application dependencies
uv pip install .
```

### 3. Configure Environment

Create `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here
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
│   ├── agent.py           # AI agent logic
│   ├── audit.py           # Audit logging
│   ├── health.py          # Health check functionality
│   ├── interface.py       # User interface
│   ├── network_device.py  # Device connection
│   ├── sensitive_data.py  # Sensitive data protection
│   ├── settings.py        # Configuration
│   └── security.py        # Command security policy
├── tests/                 # Test files
├── pyproject.toml         # Project dependencies
├── .env                   # Environment secrets
└── README.md              # This file
```

## 🏗️ Simplified Architecture

Following the refactoring plan, the architecture has been significantly simplified:

### Core Modules

| Module | Class | Responsibility |
|--------|-------|-----------------|
| `agent.py` | `Agent` | LLM integration and command orchestration |
| `network_device.py` | `DeviceConnection` | SSH connection and command execution |
| `security.py` | `CommandSecurityPolicy` | Command validation and security checks |
| `sensitive_data.py` | `SensitiveDataProtector` | Data sanitization and protection |
| `audit.py` | `AuditLogger` | Security logging and events |
| `settings.py` | `Settings` | Centralized configuration |
| `interface.py` | `UserInterface` | Interactive CLI interface |

### Removed Complexity

Per the refactoring plan, the following features were removed to simplify the architecture:

- Model fallback chain
- Local rate limiting
- Command history tracking
- Statistics tracking
- Special commands (except quit)
- Complex reconnection logic
- Metrics dashboard from core
- Overly complex configuration layers

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
GigabitEthernet0/0 is up, line protocol is up
Hardware is iGbE, address is 0011.2233.4455

GigabitEthernet0/1 is up, line protocol is up
Hardware is iGbE, address is 0011.2233.4456

GigabitEthernet0/2 is down, line protocol is down

Loopback0 is up, line protocol is up
------------------------------------------------------------

💬 Ask: quit
✓ Disconnected

📝 Audit logs saved to: logs/audit_YYYYMMDD_HHMMSS.log
```

## 🔧 Technical Stack

- **Python 3.12+** — Modern Python with type hints
- **LangChain** — LLM orchestration framework
- **Netmiko** — Network device communication
- **Pydantic** — Type-safe configuration management
- **Groq** — Fast LLM inference API
- **pytest** — Testing framework

## 🔒 Security Features

This application implements several security measures:

### **Read-Only by Design** 🔒

- Only `show`, `display`, and `get` commands are allowed
- Dangerous commands like `reload`, `write`, `configure` are blocked
- Command validation with whitelist + blacklist protection
- Command chaining protection (blocks `;`, allows safe pipes only)

### **Prompt Injection Defense** 🛡️

- Length limits (configurable in settings)
- Suspicious pattern detection and blocking
- Query sanitization for malicious content

### **Sensitive Data Protection** 🔐

- Password/API key automatic sanitization
- Automatic redaction in logs and error messages
- Configurable sensitive data patterns

### **Secure Configuration**

- Environment-based configuration
- API keys never stored in code
- Secure credential handling

## 🧪 Testing

Run the test suite to ensure everything is working:

```bash
# Run all tests
uv run pytest tests/

# Run tests with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_security.py
```

## 🎯 Use Cases

- **Network Troubleshooting** — Quick diagnostics without CLI hunting
- **Health Checks** — Regular device status verification
- **Training** — Learn networking concepts interactively
- **Documentation** — AI-generated device reports

## ✅ What's Supported

- ✅ Cisco IOS devices (routers and switches)
- ✅ SSH connections with username/password
- ✅ Show commands (read-only)
- ✅ Natural language queries
- ✅ Secure command execution
- ✅ Audit logging

## ❌ What's Not Supported

- ❌ Configuration changes (by design - security first)
- ❌ Non-Cisco devices (currently)
- ❌ Telnet connections (SSH only)

---

**Happy Automating!** 🚀🤖
