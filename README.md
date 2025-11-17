# NLP Network Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, NLP-powered network operations co-pilot designed to bridge the gap between natural language and network device management. This agent enables network administrators to diagnose and troubleshoot network issues using everyday language instead of complex CLI commands.

## ✨ Key Features

- **⚡ NLP-First Architecture:** Local spaCy NLP pre-processor instantly classifies user intent and extracts entities (devices, interfaces, protocols) for faster, more reliable interactions.
- **🧠 Multi-Agent Workflow:** Planner/Executor agent team orchestrated by LangGraph for complex, multi-step network diagnostics.
- **📄 Structured Data Contracts:** Pydantic models ensure consistent communication between all components.
- **💬 Conversational Interface:** Natural language interaction with conversational memory for follow-up questions.
- **🔌 Multi-Protocol Support:** Designed to support both traditional CLI/SSH and modern network protocols like gNMI.
- **🛡️ Built-in Security:** Command filtering and output sanitization to prevent dangerous operations.
- **📈 On-Demand Health Analysis:** Proactively analyzes device health by comparing current state to the last known state, using an LLM to identify significant changes.

## 🏗️ Architecture Overview

The agent uses a **NLP-First** architecture that processes queries through a deterministic pre-processing step before engaging the AI workflow:

```
[User Input] -> [spaCy NLP Pre-processor] -> [Structured Intent] -> [Intelligent Router] -> [LangGraph Workflow] -> [Response]
```

### Core Components:

1. **NLP Pre-processor** - Extracts intent and entities using local spaCy model
2. **Intelligent Router** - Handles simple queries and routes complex ones to the workflow
3. **LangGraph Workflow** - Multi-agent system:
   - Planner Agent: Creates execution plans from structured intents
   - Executor Agent: Runs network commands and tools
   - Generator Node: Synthesizes results into responses

## 📁 Project Structure

```
.
├── command.yaml          # NLP command mappings and keywords
├── inventory.yaml        # Network device inventory
├── main.py              # CLI entry point
├── pyproject.toml       # Project dependencies
├── README.md
└── src/
    ├── agents/          # LangGraph agents (planner, executor)
    ├── core/            # Core models and network manager
    ├── graph/           # LangGraph workflow
    ├── nlp/             # NLP preprocessor
    └── tools/           # Network tools
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

3. Install required NLP model:
```bash
python -m spacy download en_core_web_sm
```

4. Set up environment:
Create a `.env` file in the project root:
```
GROQ_API_KEY="your_groq_api_key"
```

5. Configure your network inventory in `inventory.yaml`:
```yaml
devices:
  - name: S1
    hostname: 192.168.1.10
    username: admin
    password: password
    device_type: cisco_ios
    connection_protocol: netmiko
    role: switch

  - name: R1
    hostname: 192.168.1.1
    username: admin
    password: password
    device_type: cisco_ios
    connection_protocol: netmiko
    role: router
```

## 💻 Usage

Start an interactive chat session:

```bash
uv run python main.py chat
```

Example queries:
- `show interfaces on S1`
- `list all devices`
- `show running config on R1`
- `what is the status of the interfaces on R1?`

Run a single, on-demand health analysis across all devices:

```bash
uv run python main.py analyze
```

## 🚀 Future Roadmap

- **Proactive Monitoring Service:** Evolve the `analyze` command into a continuously running service (daemon) that performs health checks on a schedule (e.g., every 15 minutes).
- **Collaborative Alerting:** Integrate a notification service to push `Critical` or `Warning` findings from the analysis to platforms like Slack or Webex, turning the agent into a true team collaborator.

## 🤝 Contributing

This project follows modern Python best practices:

- Dependency management with `uv`
- Code formatting with `ruff`
- Type checking and linting with `ruff`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
