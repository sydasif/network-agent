# AI Network Agent V3 - NLP-First Co-pilot

Welcome to Version 3, a production-ready evolution of the AI Network Agent. This version introduces a sophisticated, local NLP layer for faster, more reliable, and more intelligent network operations.

## V3 Architecture: Understand, Then Plan

The core of V3 is a new NLP-First architecture. Every user query goes through a deterministic, spaCy-powered pre-processing step before any AI reasoning is invoked.

**Flow:**
`User Input` -> `spaCy NLP Pre-processor` -> `Structured Intent` -> `Intelligent Router` -> `LangGraph Workflow` -> `Final Response`

### Key Features

- **spaCy NLP Layer:** Instantly classifies user intent and extracts entities (devices, interfaces, protocols) locally for speed and privacy.
- **Intelligent Routing:** Simple greetings or ambiguous questions are handled immediately without engaging the full agent, saving time and resources.
- **Deterministic Planning:** The Planner agent receives a structured intent, making its job of creating tool-call plans more reliable and predictable.
- **Multi-Agent Workflow (LangGraph):** Retains the powerful Planner/Executor model for handling complex, multi-step tasks.
- **Structured Pydantic Outputs:** All tools communicate using reliable Pydantic models.
- **SQLite FTS for Log Analysis:** A specialized tool uses a local SQLite database with Full-Text Search to answer questions about historical syslogs.
- **Conversational Memory:** The agent remembers the context of your conversation for natural follow-up questions.
- **Multi-Protocol Ready:** The `NetworkManager` is designed to support modern protocols like gNMI alongside traditional CLI/SSH.

## Setup Instructions

1.  **Install Dependencies:**
    Use your preferred package manager to install the dependencies listed in `pyproject.toml`.
    ```bash
    uv sync  # if using uv
    # or
    pip install -r pyproject.toml
    ```

2.  **Download NLP Model:**
    Run this command once to download the required spaCy model.
    ```bash
    python -m spacy download en_core_web_sm
    ```

3.  **Set Up Environment:**
    - Create a `.env` file in the root directory.
    - Add your Groq API key: `GROQ_API_KEY="your_api_key_here"`

4.  **Create Inventory:**
    - Edit the `inventory.yaml` file to include your network devices.

5.  **Build Log Database:**
    - Add historical logs to `syslogs.log`.
    - Run the ingestion script once to create the SQLite database with FTS for the log analysis tool.
    ```bash
    python scripts/ingest_logs.py
    ```

6.  **Run the Agent:**
    ```bash
    python main.py
    ```