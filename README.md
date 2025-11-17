# AI Network Agent : he NLP-First Network Co-pilot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Welcome to Version 3 of the AI Network Agent, a production-ready, AI-powered co-pilot designed to bridge the gap between natural language and complex network operations. This version introduces a sophisticated, local-first NLP layer for faster, more reliable, and more intelligent interactions.

This project is the culmination of extensive research into modern AI agent architectures, built with a focus on reliability, maintainability, and real-world applicability.

## ✨ Key Features

- **⚡️ spaCy NLP Layer:** Instantly classifies user intent and extracts key entities (devices, interfaces, protocols) locally for exceptional speed and privacy.
- **🧠 Intelligent Routing:** Simple greetings or ambiguous questions are handled immediately without engaging the full AI workflow, saving time and resources.
- **🔗 Multi-Agent Workflow (LangGraph):** A robust Planner/Executor agent team, orchestrated by LangGraph, decomposes and executes complex, multi-step tasks.
- **📄 Structured Data Contracts (Pydantic):** All tools and agents communicate using reliable Pydantic models, ensuring data consistency and predictable behavior.
- **🔍 Log Analysis with SQLite FTS:** A specialized tool uses a local SQLite database with Full-Text Search (FTS) to rapidly answer questions about historical syslogs, removing the need for external embedding models.
- **💬 Conversational Memory:** The agent remembers the context of your conversation, allowing for natural follow-up questions.
- **🔌 Multi-Protocol Ready:** The core `NetworkManager` is designed to support modern protocols like gNMI alongside traditional CLI/SSH via Netmiko.
- **🛡️ Built-in Security:** Includes guardrails to block potentially dangerous commands and sanitize sensitive information from outputs.

## 🏗️ V3 Architecture: Understand, Then Plan

The core of V3 is a new **NLP-First** architecture. Every user query goes through a deterministic, spaCy-powered pre-processing step before any AI reasoning is invoked. This makes the system faster, cheaper, and more reliable.

**Data Flow:**

```bash
[User Input] -> [spaCy NLP Pre-processor] -> [Structured Intent] -> [Intelligent Router] -> [LangGraph Workflow] -> [Final Response]
```

1. **NLP Pre-processor:** The user's query is instantly analyzed by a local spaCy model to determine intent and extract entities.
2. **Intelligent Router:** The main application logic inspects the structured intent. Simple cases (like greetings) are handled immediately. Ambiguous requests are rejected with a helpful prompt.
3. **LangGraph Workflow:** Only valid, understood requests are passed to the multi-agent system.
    - **Planner Agent:** Receives the structured intent and creates a step-by-step plan of tool calls.
    - **Executor Agent:** Executes the tools in the plan.
    - **Generator Node:** Synthesizes the results into a final, human-readable response.

## 📂 Directory Structure

```bash
.
├── .env
├── inventory.yaml
├── main.py
├── pyproject.toml
├── README.md
├── scripts
│   └── ingest_logs.py
├── src
│   ├── agents
│   │   ├── executor.py
│   │   └── planner.py
│   ├── core
│   │   ├── config.py
│   │   ├── models.py
│   │   └── manager.py
│   ├── graph
│   │   └── workflow.py
│   ├── nlp
│   │   └── preprocessor.py
│   └── tools
│       ├── executor.py
│       ├── inventory.py
│       └── log_analyzer.py
└── syslogs.log
```

## 🚀 Getting Started

Follow these steps to get the AI Network Agent V3 running on your local machine.

### 1. Prerequisites

- Python 3.12+
- Access to network devices via SSH.
- A Groq API key for the LLM.

### 2. Installation

Clone the repository and install the required dependencies.

```bash
# Clone the repository
git clone <your-repo-url>
cd <your-repo-directory>

# Install dependencies from pyproject.toml
pip install .```

### 3. Download NLP Model

Run this command once to download the required spaCy model for the NLP layer.

```bash
python -m spacy download en_core_web_sm
```

### 4. Set Up Environment

Create a `.env` file in the root directory of the project and add your Groq API key.

**.env**

```
GROQ_API_KEY="gsk_YourSecretGroqApiKey"
```

### 5. Configure Inventory

Edit the `inventory.yaml` file to include the network devices you want the agent to manage.

**inventory.yaml**

```yaml
devices:
  - name: S1
    hostname: 192.168.1.10
    username: your_user
    password: your_password
    device_type: cisco_ios
    connection_protocol: netmiko

  - name: R1
    hostname: 192.168.1.1
    username: your_user
    password: your_password
    device_type: cisco_ios
    connection_protocol: netmiko
```

### 6. Build Log Database

Add your historical syslog data to the `syslogs.log` file. Then, run the ingestion script once to create the searchable SQLite database.

```bash
python main.py ingest-logs
```

## 💻 Usage

The application is run via a command-line interface powered by Typer.

### Start an Interactive Chat Session

This is the main mode of operation.

```bash
python main.py chat
```

Once the agent is running, you can ask it questions in natural language.

**Example Questions:**

- `list all devices`
- `show me the vlans on S1`
- `what is the status of the interfaces on R1?`
- `check for BGP flaps on R1 and show me its version` (multi-step query)
- `were there any critical errors yesterday?` (log analysis)

### Re-ingest Logs

If you update the `syslogs.log` file, you can rebuild the database at any time with the `ingest-logs` command.

```bash
python main.py ingest-logs
```

## 🛠️ Core Components Explained

- `src/nlp/preprocessor.py`: The heart of the NLP-First architecture. Uses spaCy to convert raw text into a structured `UserIntent`.
- `src/graph/workflow.py`: The LangGraph-based multi-agent system that orchestrates planning and execution.
- `src/tools/`: Contains the individual capabilities of the agent (inventory search, command execution, log analysis).
- `src/core/`: Provides the foundational building blocks:
  - `config.py`: Centralized application settings.
  - `models.py`: Pydantic data models that act as contracts between all components.
  - `manager.py`: The robust, encapsulated service for all device interactions.
- `main.py`: The Typer-based CLI entry point for the application.

## 🗺️ Future Roadmap

This project provides a solid foundation. Future work could include:

- **Comprehensive Testing:** Building a suite of unit and integration tests.
- **CI/CD Pipeline:** Automating testing and deployment with GitHub Actions.
- **Containerization:** Packaging the application with Docker for easy deployment.
- **Tool Expansion:** Adding new tools for configuration changes (with human-in-the-loop confirmation) or integration with other systems like an IPAM or monitoring platform.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
