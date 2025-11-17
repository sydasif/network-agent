# AI Network Agent V2 - Multi-Agent Co-pilot

Welcome to Version 2, a significant evolution of the AI Network Agent. This version introduces a sophisticated multi-agent architecture with LangGraph, structured data contracts using Pydantic, and a specialized RAG system for historical log analysis.

## V2 Architecture: Multi-Agent Workflow

The core of V2 is a planner-executor architecture orchestrated by LangGraph. This enables complex, multi-step tasks to be decomposed and executed reliably.

**Flow:**
`User Input` -> `Planner Agent` -> `Tool Execution` -> `Response Generation` -> `Final Response`

### Key Features

- **Multi-Agent Architecture:** Planner and Executor agents work together to handle complex, multi-step network operations.
- **Structured Data Contracts:** All tools communicate using reliable Pydantic models for consistent data exchange.
- **Conversational Memory:** The agent remembers the context of your conversation for natural follow-up questions.
- **SQLite FTS for Log Analysis:** A specialized tool uses a local SQLite database with Full-Text Search (FTS) to answer questions about historical syslogs.
- **Multi-Protocol Ready:** The `NetworkManager` is designed to support modern protocols like gNMI alongside traditional CLI/SSH.
- **Enhanced Security:** Improved command sanitization and dangerous command blocking.

## Setup Instructions

1.  **Install Dependencies:**
    Use your preferred package manager to install the dependencies listed in `pyproject.toml`.
    ```bash
    uv sync  # if using uv
    # or
    pip install -r pyproject.toml
    ```

2.  **Set Up Environment:**
    - Create a `.env` file in the root directory.
    - Add your Groq API key: `GROQ_API_KEY="your_api_key_here"`

3.  **Create Inventory:**
    - Edit the `inventory.yaml` file to include your network devices with the new `connection_protocol` field.

4.  **Build Log Database:**
    - Add historical logs to `syslogs.log`.
    - Run the ingestion script once to create the SQLite database with FTS for the log analysis tool.
    ```bash
    python scripts/ingest_logs.py
    ```

5.  **Run the Agent:**
    ```bash
    python main.py
    ```