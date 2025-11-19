# Simplified NLP Network Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**⚠️ SECURITY NOTICE: This project requires security hardening before production use. See SECURITY.md for details.**

A simplified, NLP-powered network operations agent designed to bridge the gap between natural language and network device management. This agent enables network administrators to execute network commands using everyday language, powered by LangChain and Nornir.

## ✨ Key Features

- **⚡ Simple NLP Integration:** Uses LangChain's structured output for direct command interpretation.
- **🔌 Nornir-Powered:** Leverages Nornir for device inventory management, connection handling, and command execution.
- **📄 Minimal Data Models:** Simplified Pydantic models for essential data contracts.
- **💬 Conversational Interface:** Natural language interaction with a streamlined response system.
- **🛡️ Basic Security:** Simple command execution with connection management.

## 🏗️ Architecture Overview

The agent uses a **Simple NLP-to-Command** architecture:

```
[User Input] -> [LLM Structured Output] -> [Device & Command Extraction] -> [Nornir Command Execution] -> [Response]
```

### Core Components:

1. **SimpleNetworkAgent** - Single agent that processes natural language input and executes commands
2. **NetworkManager** - Uses Nornir for device inventory and connection management
3. **LangChain Integration** - Direct LLM interaction with structured output for command extraction

## 📁 Project Structure

```
.
├── inventory/           # Nornir inventory files
│   ├── hosts.yaml      # Device inventory
│   ├── groups.yaml     # Device groups
│   ├── defaults.yaml   # Default connection settings
│   └── config.yaml     # Nornir configuration
├── main.py            # CLI entry point
├── pyproject.toml     # Project dependencies
├── README.md
├── SECURITY.md        # Security considerations
├── uv.lock            # Dependency lock file
├── src/
│   ├── __init__.py    # Package initialization
│   ├── agents/        # AI agent implementations
│   │   ├── __init__.py # Agents package
│   │   └── simple_agent.py # Simplified AI agent
│   └── core/          # Core system components
│       ├── __init__.py # Core package
│       ├── config.py  # Configuration settings
│       ├── models.py  # Simplified data models
│       └── network_manager.py # Nornir-based network management
└── tests/             # Test suite
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Network device access via SSH
- Groq API key for LLM access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nlp-network-agent
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up environment:
Create a `.env` file in the project root:
```
GROQ_API_KEY="your_groq_api_key"
```

4. Configure your network inventory in `inventory/hosts.yaml`:
```yaml
R1:
  hostname: 192.168.1.10
  username: admin
  password: admin123
  platform: cisco_ios
  groups: [core_routers]
  data:
    role: core
    site: main
```

## 💻 Usage

Start an interactive chat session:

```bash
uv run python main.py chat
```

Example queries:
- `show interfaces on S1`
- `show version on R1`
- `show running config on R1`

## 🛠️ Technical Architecture

### Core Modules

- **src.core.models**: Defines minimal Pydantic data models for the simplified application
- **src.core.config**: Simplified configuration settings using Pydantic Settings with support for environment variables and .env files
- **src.core.network_manager**: Nornir-based network device management
- **src.agents.simple_agent**: Simplified AI agent that processes requests and uses Nornir for execution

### Data Flow

1. **Input Processing**: User queries are processed by the LLM's structured output feature which returns:
   - Device name to execute the command on
   - Network command to execute

2. **Command Execution**: The SimpleNetworkAgent:
   - Extracts device and command using the LLM
   - Executes the command using Nornir
   - Returns the result to the user

## 📚 API Reference

### Command-Line Interface

The agent provides a Typer-based CLI with the following command:

#### `chat`
Starts an interactive chat session with the network agent
```
uv run python main.py chat
```

### Core Classes

#### `SimpleNetworkAgent`
Simple NLP agent for processing network queries.

- `__init__(api_key: str)`: Initialize with Groq API key
- `process_request(user_input: str) -> Dict[str, str]`: Process natural language request and return command output

#### `NetworkManager`
Manages network device connections and command execution using Nornir.

- `__init__(config_file: str = "inventory/config.yaml")`: Initialize with Nornir config
- `execute_command(device_name: str, command: str) -> str`: Execute CLI command on device
- `close_all_sessions()`: Close all active connections

## 🚀 Future Roadmap

- **Enhanced NLP:** Add support for more complex natural language queries
- **Multi-device Operations:** Execute commands across multiple devices simultaneously
- **Command History:** Add history and recall functionality

## 🤝 Contributing

This project follows modern Python best practices:

- Dependency management with `uv`
- Code formatting with `ruff`
- Type checking and linting with `ruff`

Before submitting changes:
1. Run `ruff check --fix . && ruff format .` to format code
2. Run tests to ensure functionality
3. Add documentation for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
