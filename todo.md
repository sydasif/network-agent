# Vision for Version 2: The Network Operations Co-pilot

This is not just an update; it is a complete transformation that directly implements the advanced concepts from your research. It moves from a simple, stateless agent to a sophisticated, stateful, multi-agent system ready for complex network operations.

---

This new version embodies the following principles from your research:

1. **Multi-Agent Architecture (`sp_oncall`, `AGNTCY`):** The single agent is replaced by a **LangGraph**-powered workflow. A `Planner` agent decomposes tasks, and an `Executor` agent carries them out. This is more robust and scalable.
2. **Structured Data (`Pydantic`):** All tools now return structured Pydantic models instead of raw strings. This makes the agent's behavior far more reliable and predictable, as seen in the `unlocking-ai-agents` project. The old `parser.py` tool has been completely removed.
3. **Persistent Memory (`mistral-4-cisco`):** The agent is now stateful, remembering the context of the conversation to allow for natural follow-up questions.
4. **Specialized RAG Tool (`syslog_gpt`):** A new tool has been added for log analysis, implementing the Retrieval-Augmented Generation (RAG) pattern with a local vector database (ChromaDB) to answer historical questions.
5. **Modern Protocol Ready (`sp_oncall`):** The `NetworkManager` has been refactored to support different connection protocols, preparing it for modern interfaces like gNMI alongside Netmiko.
6. **Observability & Maintainability:** The code is more modular, making it easier to debug, maintain, and extend.

---

## New Directory Structure for Version 2

```
.
├── inventory.yaml
├── main.py
├── pyproject.toml
├── README_V2.md
├── scripts
│   └── ingest_logs.py
├── src
│   ├── agents
│   │   ├── __init__.py
│   │   ├── executor.py
│   │   └── planner.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── network_manager.py
│   ├── graph
│   │   ├── __init__.py
│   │   └── workflow.py
│   └── tools
│       ├── __init__.py
│       ├── executor.py
│       ├── inventory.py
│       └── log_analyzer.py
└── syslogs.log
```

---

### The Complete Code for Version 2

Here is the full, rewritten codebase.

#### **File: `pyproject.toml`** (Updated Dependencies)

```toml
[project]
name = "network-agent-v2"
version = "2.0.0"
requires-python = ">=3.12"
dependencies = [
    "groq>=0.33.0",
    "langchain>=0.2.0,<0.3.0",
    "langchain-groq>=0.1.0,<0.2.0",
    "langgraph>=0.1.0,<0.2.0",
    "netmiko>=4.6.0",
    "python-dotenv>=1.2.1",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    # New dependencies for V2
    "langchain-community>=0.2.0", # For text splitters and local embeddings
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0", # For local embeddings
]

[tool.ruff]
line-length = 88
```

#### **File: `inventory.yaml`** (Adjusted for Protocols)

```yaml
devices:
  - name: S1
    hostname: 192.168.121.101
    username: admin
    password: admin
    device_type: cisco_ios
    description: Floor 1 Distribution Switch
    role: distribution
    connection_protocol: netmiko # New field

  - name: S2
    hostname: 192.168.121.102
    username: admin
    password: admin
    device_type: cisco_ios
    description: Floor 2 Distribution Switch
    role: distribution
    connection_protocol: netmiko # New field

  - name: core-router-gnmi
    hostname: 10.0.0.1
    username: cisco
    password: cisco
    device_type: cisco_xr
    description: Core router with gNMI support
    role: core
    connection_protocol: gnmi # Example for a modern device
```

#### **File: `syslogs.log`** (New Sample Data for RAG)

```log
2025-11-17 10:00:01 S1 %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/1, changed state to down
2025-11-17 10:00:03 S1 %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/1, changed state to up
2025-11-17 10:05:22 S2 %SYS-5-CONFIG_I: Configured from console by admin on vty0 (192.168.121.1)
2025-11-17 11:30:00 S1 %BGP-5-ADJCHANGE: neighbor 10.1.1.2 Down User reset
2025-11-17 11:30:45 S1 %BGP-5-ADJCHANGE: neighbor 10.1.1.2 Up
2025-11-17 12:00:00 S2 %SPANTREE-2-BLOCK_PVID_LOCAL: Blocking GigabitEthernet0/3 on VLAN0010. Inconsistent peer vlan.
2025-11-17 12:01:00 S2 %SPANTREE-2-UNBLOCK_PVID_LOCAL: Unblocking GigabitEthernet0/3 on VLAN0010. Peer vlan restored.
```

#### **File: `src/core/models.py`** (New - For Structured Data)

```python
"""Pydantic models for structured tool outputs."""
from typing import List, Optional
from pydantic import BaseModel, Field

class DeviceInfo(BaseModel):
    """Data model for a single network device."""
    name: str = Field(..., description="The name of the device.")
    hostname: str = Field(..., description="The IP address or hostname.")
    role: Optional[str] = Field(None, description="The role of the device in the network.")
    device_type: str = Field(..., description="The Netmiko device type (e.g., cisco_ios).")

class CommandOutput(BaseModel):
    """Structured output for a network command."""
    device_name: str = Field(..., description="The device the command was run on.")
    command: str = Field(..., description="The command that was executed.")
    output: str = Field(..., description="The raw, sanitized output from the device.")
    status: str = Field("success", description="Either 'success' or 'error'.")
    error_message: Optional[str] = Field(None, description="Details if an error occurred.")

class LogAnalysisOutput(BaseModel):
    """Structured output for a log analysis query."""
    query: str = Field(..., description="The original user query for the logs.")
    relevant_logs: List[str] = Field(..., description="A list of the most relevant log entries found.")
    summary: str = Field(..., description="A brief summary of the findings from the logs.")
```

#### **File: `src/core/network_manager.py`** (Rewritten)

```python
"""Core module for managing network device connections and commands."""
import re
from typing import Dict, Optional
from dataclasses import dataclass, field
import yaml
from netmiko import ConnectHandler

@dataclass
class Device:
    """Represents a network device with connection details."""
    name: str
    hostname: str
    username: str
    password: str
    device_type: str
    description: str = ""
    role: str = ""
    connection_protocol: str = "netmiko"

class NetworkManager:
    """Manages inventory, connections, and command execution for network devices."""
    def __init__(self, inventory_file: str = "inventory.yaml"):
        self.inventory_file = inventory_file
        self.devices: Dict[str, Device] = self._load_inventory()
        self.sessions: Dict[str, ConnectHandler] = {}

    def _load_inventory(self) -> Dict[str, Device]:
        """Loads device inventory from a YAML file."""
        try:
            with open(self.inventory_file, "r") as f:
                data = yaml.safe_load(f)
            return {
                dev_data["name"]: Device(**dev_data)
                for dev_data in data.get("devices", [])
            }
        except Exception as e:
            print(f"Error loading inventory: {e}")
            return {}

    def get_device(self, device_name: str) -> Optional[Device]:
        """Retrieves a device by its name."""
        return self.devices.get(device_name)

    def execute_command(self, device_name: str, command: str) -> str:
        """
        Executes a command on a device, dispatching to the correct protocol handler.
        """
        device = self.get_device(device_name)
        if not device:
            raise ValueError(f"Device '{device_name}' not found in inventory.")

        if device.connection_protocol == "netmiko":
            return self._execute_netmiko_command(device, command)
        elif device.connection_protocol == "gnmi":
            return self._execute_gnmi_get(device, command)
        else:
            raise NotImplementedError(f"Protocol '{device.connection_protocol}' is not supported.")

    def _execute_netmiko_command(self, device: Device, command: str) -> str:
        """Executes a command using Netmiko (CLI/SSH)."""
        if self._is_dangerous_command(command):
            raise ValueError(f"Execution blocked for potentially dangerous command: {command}")

        if device.name not in self.sessions:
            self.sessions[device.name] = ConnectHandler(
                device_type=device.device_type,
                host=device.hostname,
                username=device.username,
                password=device.password,
                timeout=10,
            )

        session = self.sessions[device.name]
        output = session.send_command(command, read_timeout=20)
        return self._sanitize_output(output)

    def _execute_gnmi_get(self, device: Device, xpath: str) -> str:
        """Placeholder for executing a gNMI GET request."""
        # In a real implementation, you would use a library like pygnmi here.
        # For now, this demonstrates the dispatcher pattern.
        raise NotImplementedError(
            f"gNMI not implemented. Attempted to query {device.name} with path: {xpath}"
        )

    def _is_dangerous_command(self, command: str) -> bool:
        """Checks for potentially harmful commands."""
        dangerous_patterns = [r"write\s+erase", r"reload", r"delete", r"format", r"configure\s+terminal"]
        command_lower = command.lower().strip()
        return any(re.search(pattern, command_lower) for pattern in dangerous_patterns)

    def _sanitize_output(self, output: str) -> str:
        """Removes sensitive information from CLI output."""
        # Simplified for brevity; a production version would be more robust.
        output = re.sub(r"password\s+\S+", "password [REDACTED]", output, flags=re.IGNORECASE)
        output = re.sub(r"secret\s+\S+", "secret [REDACTED]", output, flags=re.IGNORECASE)
        return output

    def close_all_sessions(self):
        """Closes all active Netmiko sessions."""
        for session in self.sessions.values():
            if session.is_alive():
                session.disconnect()
        self.sessions.clear()
```

#### **File: `src/tools/inventory.py`** (Rewritten)

```python
"""Tool for searching the network device inventory."""
from typing import List
from langchain_core.tools import tool
from src.core.models import DeviceInfo
from src.core.network_manager import NetworkManager

# Initialize a single NetworkManager instance to be shared by tools
network_manager = NetworkManager("inventory.yaml")

@tool
def inventory_search(device_name: str = "") -> List[DeviceInfo]:
    """
    Searches the inventory for devices. If no name is provided, lists all devices.
    Use this to find device names, roles, or hostnames.
    """
    devices_to_return = []
    if device_name:
        device = network_manager.get_device(device_name)
        if device:
            devices_to_return.append(DeviceInfo(**device.__dict__))
    else:
        devices_to_return = [
            DeviceInfo(**dev.__dict__) for dev in network_manager.devices.values()
        ]
    return devices_to_return
```

#### **File: `src/tools/executor.py`** (Rewritten)

```python
"""Tool for executing network commands."""
from langchain_core.tools import tool
from src.core.models import CommandOutput
from src.tools.inventory import network_manager # Reuse the same instance

@tool
def run_network_command(device_name: str, command: str) -> CommandOutput:
    """
    Executes a read-only CLI command on a specified network device.
    Use this for 'show' commands to get operational status or configuration.
    """
    try:
        output = network_manager.execute_command(device_name, command)
        return CommandOutput(device_name=device_name, command=command, output=output)
    except Exception as e:
        return CommandOutput(
            device_name=device_name,
            command=command,
            output="",
            status="error",
            error_message=str(e),
        )
```

#### **File: `src/tools/log_analyzer.py`** (New)

```python
"""Tool for analyzing historical syslog data using RAG."""
import chromadb
from langchain_core.tools import tool
from langchain_community.embeddings import OllamaEmbeddings
from src.core.models import LogAnalysisOutput

# Setup for the RAG tool
DB_PATH = "./chroma_db"
COLLECTION_NAME = "syslogs"

@tool
def analyze_logs(query: str) -> LogAnalysisOutput:
    """
    Analyzes historical syslogs to answer questions about past network events.
    Use this when the user asks about errors, flaps, changes, or events that happened in the past.
    """
    try:
        # Use a local LLM for embeddings for privacy and cost-effectiveness
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)

        # Query the vector store
        results = collection.query(
            query_embeddings=embeddings.embed_query(query),
            n_results=5,
        )

        relevant_logs = results["documents"][0] if results["documents"] else []

        if not relevant_logs:
            summary = "No relevant logs found for that query."
        else:
            summary = "Found several relevant log entries. Please review the provided logs."

        return LogAnalysisOutput(
            query=query,
            relevant_logs=relevant_logs,
            summary=summary
        )
    except Exception as e:
        # This can happen if the DB doesn't exist yet
        return LogAnalysisOutput(
            query=query,
            relevant_logs=[],
            summary=f"Error analyzing logs: {e}. Please ensure the log database has been created by running 'scripts/ingest_logs.py'."
        )
```

#### **File: `scripts/ingest_logs.py`** (New)

```python
"""One-time script to process and ingest syslogs into the vector database."""
import chromadb
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import CharacterTextSplitter

# Configuration
LOG_FILE_PATH = "./syslogs.log"
DB_PATH = "./chroma_db"
COLLECTION_NAME = "syslogs"

def main():
    """Loads, splits, and ingests logs into ChromaDB."""
    print("Starting log ingestion process...")

    # 1. Load the log file
    loader = TextLoader(LOG_FILE_PATH)
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s) from {LOG_FILE_PATH}")

    # 2. Split the document into chunks (each log line is a chunk)
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)
    print(f"Split document into {len(docs)} chunks.")

    # 3. Initialize embeddings model (using a local model)
    print("Initializing embeddings model (Ollama)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    print("Embeddings model initialized.")

    # 4. Setup ChromaDB client and create a collection
    client = chromadb.PersistentClient(path=DB_PATH)
    # Delete collection if it exists to avoid duplicates
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection: '{COLLECTION_NAME}'")

    collection = client.create_collection(name=COLLECTION_NAME)
    print(f"Created new collection: '{COLLECTION_NAME}'")

    # 5. Ingest documents into the collection
    print("Ingesting documents into ChromaDB...")
    collection.add(
        documents=[doc.page_content for doc in docs],
        ids=[str(i) for i in range(len(docs))]
    )
    print("✅ Ingestion complete!")
    print(f"Vector database created at: {DB_PATH}")

if __name__ == "__main__":
    main()```

#### **File: `src/agents/planner.py`** (New)

```python
"""Defines the Planner Agent for the LangGraph workflow."""
from langchain_core.prompts import ChatPromptTemplate

PLANNER_PROMPT = """
You are an expert network operations planner. Your job is to create a step-by-step plan to answer the user's request.
You will be given the user's question and the conversation history.

**Rules:**
1.  **Decompose:** Break down the user's request into a sequence of tool calls.
2.  **No Execution:** You DO NOT execute tools. You only create the plan.
3.  **Tool Selection:** Choose the best tool for each step:
    - `inventory_search`: To find device names, roles, or see what devices are available.
    - `run_network_command`: To execute a 'show' command on a specific device.
    - `analyze_logs`: To investigate historical events, errors, or past issues using syslogs.
4.  **Clarity:** Each step in your plan must be a clear, valid tool call.
5.  **Reasoning:** Briefly explain your reasoning for the plan.

**Example:**
User Question: "What is the status of the interfaces on S1 and were there any BGP flaps yesterday?"

Your Plan:
{
  "plan": [
    {
      "tool": "run_network_command",
      "args": {"device_name": "S1", "command": "show ip interface brief"}
    },
    {
      "tool": "analyze_logs",
      "args": {"query": "BGP flaps on S1 yesterday"}
    }
  ],
  "reasoning": "First, I will check the current interface status on S1. Then, I will analyze the historical logs to check for any BGP flaps as requested."
}

Now, create a plan for the following request.
"""

def get_planner():
    """Creates the planner agent components."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_PROMPT),
        ("human", "User Question: {input}\n\nConversation History:\n{chat_history}")
    ])
    return prompt
```

#### **File: `src/agents/executor.py`** (New)

```python
"""Defines the Tool Executor for the LangGraph workflow."""
from typing import List, Dict, Any
from src.tools.inventory import inventory_search
from src.tools.executor import run_network_command
from src.tools.log_analyzer import analyze_logs

# Map tool names to their functions
TOOLS = {
    "inventory_search": inventory_search,
    "run_network_command": run_network_command,
    "analyze_logs": analyze_logs,
}

def tool_executor(plan: List[Dict[str, Any]]) -> List[Any]:
    """
    Executes a list of tool calls from the planner's plan.
    """
    results = []
    for step in plan:
        tool_name = step.get("tool")
        tool_args = step.get("args", {})

        if tool_name in TOOLS:
            tool_function = TOOLS[tool_name]
            try:
                result = tool_function.invoke(tool_args)
                results.append(result)
            except Exception as e:
                results.append(f"Error executing tool {tool_name}: {e}")
        else:
            results.append(f"Unknown tool: {tool_name}")

    return results
```

#### **File: `src/graph/workflow.py`** (New - The Core Orchestrator)

```python
"""The core LangGraph workflow for the multi-agent system."""
import json
from typing import List, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from src.agents.planner import get_planner
from src.agents.executor import tool_executor

# Define the state for our graph
class AgentState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    plan: List[dict]
    tool_results: List[any]
    response: str

class NetworkWorkflow:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.1-8b-instant", temperature=0.0)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Builds the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # 1. Planner Node
        workflow.add_node("planner", self.planner_node)

        # 2. Tool Executor Node
        workflow.add_node("executor", self.executor_node)

        # 3. Response Generator Node
        workflow.add_node("generator", self.generator_node)

        # Define the edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "generator")
        workflow.add_edge("generator", END)

        return workflow.compile()

    def planner_node(self, state: AgentState):
        """Generates the initial plan."""
        prompt = get_planner()
        planner_chain = prompt | self.llm
        response = planner_chain.invoke(state)
        plan = json.loads(response.content).get("plan", [])
        return {"plan": plan}

    def executor_node(self, state: AgentState):
        """Executes the tools based on the plan."""
        plan = state["plan"]
        results = tool_executor(plan)
        return {"tool_results": results}

    def generator_node(self, state: AgentState):
        """Generates the final response to the user."""
        context = f"""
        User Question: {state['input']}
        Plan: {state['plan']}
        Tool Results: {[res.dict() if hasattr(res, 'dict') else res for res in state['tool_results']]}

        Based on the plan and the results from the tools, provide a clear, concise, and friendly answer to the user's original question.
        Synthesize the information from all tool results into a single, coherent response.
        """
        response = self.llm.invoke(context)
        return {"response": response.content}

    def run(self, query: str, chat_history: List[BaseMessage]):
        """Runs the workflow."""
        inputs = {"input": query, "chat_history": chat_history}
        final_state = self.graph.invoke(inputs)
        return final_state["response"]```

#### **File: `main.py`** (Rewritten for V2)

```python
"""Main entry point for the AI Network Agent V2."""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from src.graph.workflow import NetworkWorkflow
from src.tools.inventory import network_manager

def main():
    """Initializes and runs the multi-agent network co-pilot."""
    load_dotenv()
    print("🤖 AI Network Agent V2 - Multi-Agent Co-pilot")
    print("=" * 60)

    # 1. Check for API Key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("⚠️ GROQ_API_KEY environment variable not set! Please set it in a .env file.")
        return

    # 2. Check for Inventory File
    if not Path("inventory.yaml").exists():
        print("⚠️ Inventory file 'inventory.yaml' not found. Please create one.")
        return
    print(f"📦 Inventory loaded: {len(network_manager.devices)} devices found.")

    # 3. Check for Log Database
    if not Path("./chroma_db").exists():
        print("⚠️ Syslog vector database not found.")
        print("💡 Run 'python scripts/ingest_logs.py' to create it before asking historical questions.")

    # 4. Initialize the Workflow
    try:
        workflow = NetworkWorkflow(api_key=groq_api_key)
        print("✅ Agent workflow initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing workflow: {e}")
        return

    print("\n💡 Ask complex questions like 'show interfaces on S1 and check for recent flaps'")
    print("   Type 'quit' or 'exit' to end the session.")
    print("=" * 60)

    chat_history = []
    while True:
        try:
            question = input("\n💬 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not question:
            continue
        if question.lower() in ["quit", "exit"]:
            break

        print("-" * 40)
        try:
            response = workflow.run(question, chat_history)
            print(f"\n🤖 Agent: {response}")
            chat_history.append(HumanMessage(content=question))
            chat_history.append(AIMessage(content=response))
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
        print("-" * 40)

    # Clean up sessions
    network_manager.close_all_sessions()
    print("\n👋 All network sessions closed. Goodbye!")

if __name__ == "__main__":
    main()
```

---

### How to Run Version 2

1. **Install Dependencies:**

    ```bash
    pip install -r pyproject.toml
    ```

    *(Note: This is a conceptual command. Use your preferred package manager like `pip` or `uv` to install the dependencies listed in `pyproject.toml`)*

2. **Set Up Environment:**
    * Create a `.env` file in the root directory.
    * Add your Groq API key to it: `GROQ_API_KEY="your_api_key_here"`
    * Ensure you have **Ollama** running with the `nomic-embed-text` model pulled (`ollama pull nomic-embed-text`).

3. **Create the Log Database:**
    * Run the ingestion script once to create the vector store for the RAG tool.

    ```bash
    python scripts/ingest_logs.py
    ```

4. **Run the Agent:**
    * Start the main application.

    ```bash
    python main.py
    ```

You now have a Version 2 that is not only more powerful and aligned with your research but is also architected to be easily extended in the future.

### Vision for Version 3: The NLP-First Network Co-pilot

This version is the culmination of our entire discussion. It integrates every feature from Version 2 and elevates the architecture with the fast, local, and powerful spaCy-based NLP layer we designed. This is not just an update; it is a refactoring for production-readiness, emphasizing speed, reliability, and intelligence.

Version 3 operates on a new, more intelligent principle: **Understand, then Plan.**

1. **NLP-First Architecture:** Every user query is first processed by a local, spaCy-powered NLP layer. This layer instantly classifies the user's **Intent** (e.g., `get_status`) and extracts key **Entities** (e.g., `device=S1`, `interface=Gi0/1`).
2. **Intelligent Routing:** The system can now make smart decisions *before* engaging the complex agentic workflow. Simple greetings are answered instantly. Ambiguous queries are rejected with a helpful message. Only valid, understood requests are passed to the agent.
3. **Deterministic Planning:** The Planner agent's job is now much simpler and more reliable. Instead of interpreting raw language, it receives a structured `UserIntent` object and its sole job is to translate that into a sequence of tool calls.
4. **All V2 Features Retained:** The powerful multi-agent LangGraph workflow, structured Pydantic outputs, conversational memory, and the RAG-based log analysis tool are all preserved and enhanced by the new NLP front-end.
5. **Speed and Privacy:** By handling the initial NLP processing locally with spaCy, the agent is faster, more responsive, and keeps all user queries private until a valid plan requires execution.

---

### New Directory Structure for Version 3

The structure is clean and reflects the new architecture.

```
.
├── .env
├── inventory.yaml
├── main.py
├── pyproject.toml
├── README_V3.md
├── scripts
│   └── ingest_logs.py
├── src
│   ├── agents
│   │   ├── __init__.py
│   │   ├── executor.py
│   │   └── planner.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── network_manager.py
│   ├── graph
│   │   ├── __init__.py
│   │   └── workflow.py
│   ├── nlp
│   │   ├── __init__.py
│   │   └── preprocessor.py
│   └── tools
│       ├── __init__.py
│       ├── executor.py
│       ├── inventory.py
│       └── log_analyzer.py
└── syslogs.log
```

---

### The Complete Code for Version 3

Here is the full, rewritten codebase for your final project.

#### **File: `pyproject.toml`** (Final Dependencies)

```toml
[project]
name = "network-agent-v3"
version = "3.0.0"
requires-python = ">=3.12"
dependencies = [
    "groq>=0.33.0",
    "langchain>=0.2.0,<0.3.0",
    "langchain-groq>=0.1.0,<0.2.0",
    "langgraph>=0.1.0,<0.2.0",
    "netmiko>=4.6.0",
    "python-dotenv>=1.2.1",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "langchain-community>=0.2.0",
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0",
    # New dependency for V3
    "spacy>=3.7.0",
]

[tool.ruff]
line-length = 88
```

#### **File: `README_V3.md`** (New)

```markdown
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
- **RAG for Log Analysis:** A specialized tool uses a local vector database (ChromaDB) to answer questions about historical syslogs.
- **Conversational Memory:** The agent remembers the context of your conversation for natural follow-up questions.
- **Multi-Protocol Ready:** The `NetworkManager` is designed to support modern protocols like gNMI alongside traditional CLI/SSH.

## Setup Instructions

1.  **Install Dependencies:**
    Use your preferred package manager to install the dependencies listed in `pyproject.toml`.
    ```bash
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
    - Ensure you have **Ollama** running with the `nomic-embed-text` model pulled (`ollama pull nomic-embed-text`) for the log analysis tool.

4.  **Create Inventory:**
    - Edit the `inventory.yaml` file to include your network devices.

5.  **Build Log Database:**
    - Add historical logs to `syslogs.log`.
    - Run the ingestion script once to create the vector database for the RAG tool.
    ```bash
    python scripts/ingest_logs.py
    ```

6.  **Run the Agent:**
    ```bash
    python main.py
    ```
```

#### **File: `src/core/models.py`** (Updated with NLP Models)

```python
"""Pydantic models for structured data contracts across the application."""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# --- Tooling Models ---

class DeviceInfo(BaseModel):
    """Data model for a single network device."""
    name: str = Field(..., description="The name of the device.")
    hostname: str = Field(..., description="The IP address or hostname.")
    role: Optional[str] = Field(None, description="The role of the device in the network.")
    device_type: str = Field(..., description="The Netmiko device type (e.g., cisco_ios).")

class CommandOutput(BaseModel):
    """Structured output for a network command."""
    device_name: str = Field(..., description="The device the command was run on.")
    command: str = Field(..., description="The command that was executed.")
    output: str = Field(..., description="The raw, sanitized output from the device.")
    status: str = Field("success", description="Either 'success' or 'error'.")
    error_message: Optional[str] = Field(None, description="Details if an error occurred.")

class LogAnalysisOutput(BaseModel):
    """Structured output for a log analysis query."""
    query: str = Field(..., description="The original user query for the logs.")
    relevant_logs: List[str] = Field(..., description="A list of the most relevant log entries found.")
    summary: str = Field(..., description="A brief summary of the findings from the logs.")

# --- NLP Pre-processing Models ---

class ExtractedEntities(BaseModel):
    """Represents the entities extracted from the user's query."""
    device_names: Optional[List[str]] = Field(None, description="A list of device hostnames, like ['S1', 'core-router-gnmi']")
    interfaces: Optional[List[str]] = Field(None, description="A list of interface names, like ['GigabitEthernet0/1']")
    protocols: Optional[List[str]] = Field(None, description="A list of networking protocols, like ['BGP', 'OSPF']")
    keywords: Optional[List[str]] = Field(None, description="Other key terms like 'flaps', 'errors', 'config'")

class UserIntent(BaseModel):
    """The structured representation of a user's request, generated by the NLP layer."""
    query: str = Field(..., description="The original, unmodified user query.")
    intent: Literal[
        "get_status", "get_config", "find_device", "troubleshoot_history", "greeting", "unknown"
    ] = Field(..., description="The primary goal of the user.")
    entities: ExtractedEntities = Field(..., description="All named entities recognized in the query.")
    sentiment: Literal["normal", "urgent", "critical"] = Field("normal", description="The inferred urgency of the user's request.")
    is_ambiguous: bool = Field(False, description="True if the query is unclear or lacks necessary information.")
```

#### **File: `src/nlp/preprocessor.py`** (New spaCy-powered version)

```python
"""
NLP Pre-processing Layer using spaCy for fast, local, and deterministic
Intent Classification and Named Entity Recognition.
"""
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from typing import List, Dict
from src.core.models import UserIntent, ExtractedEntities
from src.tools.inventory import network_manager # Import to get the device list

class NLPPreprocessor:
    def __init__(self):
        """Initializes the spaCy model, matchers, and intent rules."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Please run: python -m spacy download en_core_web_sm")
            raise

        self.intent_rules: Dict[str, List[str]] = {
            "get_status": ["show", "what is", "check", "display", "status", "version", "uptime"],
            "get_config": ["config", "configuration", "running-config", "startup-config"],
            "find_device": ["find", "list", "search", "which devices", "all devices"],
            "troubleshoot_history": ["history", "log", "logs", "past", "error", "errors", "flap", "flaps", "yesterday", "last night"],
            "greeting": ["hello", "hi", "hey", "greetings"],
        }

        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        device_names = list(network_manager.devices.keys())
        device_patterns = [self.nlp.make_doc(name) for name in device_names]
        self.phrase_matcher.add("DEVICE", device_patterns)

        protocols = ["bgp", "ospf", "eigrp", "spanning-tree", "stp", "vlan"]
        protocol_patterns = [self.nlp.make_doc(p) for p in protocols]
        self.phrase_matcher.add("PROTOCOL", protocol_patterns)

        keywords = ["flaps", "errors", "config", "down", "up", "critical"]
        keyword_patterns = [self.nlp.make_doc(k) for k in keywords]
        self.phrase_matcher.add("KEYWORD", keyword_patterns)

        interface_pattern = [{"TEXT": {"REGEX": r"([Gg]i|[Ff]a|[Ee]th|[Tt]en)[a-zA-Z]*\d+([/]\d+)*([.]\d+)?"}}]
        self.matcher.add("INTERFACE", [interface_pattern])

    def _classify_intent(self, doc) -> str:
        query_lower = doc.text.lower()
        for intent, keywords in self.intent_rules.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        return "unknown"

    def _extract_entities(self, doc) -> ExtractedEntities:
        matches = self.matcher(doc) + self.phrase_matcher(doc)
        entities = ExtractedEntities(device_names=[], interfaces=[], protocols=[], keywords=[])

        for match_id, start, end in matches:
            span = doc[start:end]
            entity_label = self.nlp.vocab.strings[match_id]

            if entity_label == "DEVICE" and span.text not in entities.device_names:
                entities.device_names.append(span.text)
            elif entity_label == "INTERFACE" and span.text not in entities.interfaces:
                entities.interfaces.append(span.text)
            elif entity_label == "PROTOCOL" and span.text.lower() not in entities.protocols:
                entities.protocols.append(span.text.lower())
            elif entity_label == "KEYWORD" and span.text.lower() not in entities.keywords:
                entities.keywords.append(span.text.lower())

        return entities

    def process(self, query: str) -> UserIntent:
        doc = self.nlp(query)
        intent = self._classify_intent(doc)
        entities = self._extract_entities(doc)
        is_ambiguous = (intent in ["get_status", "get_config"] and not entities.device_names)
        sentiment = "urgent" if "urgent" in query.lower() or "down" in query.lower() else "normal"

        return UserIntent(
            query=query, intent=intent, entities=entities, sentiment=sentiment, is_ambiguous=is_ambiguous
        )
```

#### **File: `src/graph/workflow.py`** (Adjusted for Structured Input)

```python
"""The core LangGraph workflow for the multi-agent system."""
import json
from typing import List, TypedDict
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from src.agents.planner import get_planner_prompt
from src.agents.executor import tool_executor
from src.core.models import UserIntent

class AgentState(TypedDict):
    """Defines the state of the graph."""
    input: UserIntent
    chat_history: List[BaseMessage]
    plan: List[dict]
    tool_results: List[any]
    response: str

class NetworkWorkflow:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.1-8b-instant", temperature=0.0)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("executor", self.executor_node)
        workflow.add_node("generator", self.generator_node)
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "generator")
        workflow.add_edge("generator", END)
        return workflow.compile()

    def planner_node(self, state: AgentState):
        prompt = get_planner_prompt()
        planner_chain = prompt | self.llm
        response = planner_chain.invoke({
            "input": state["input"].json(indent=2),
            "chat_history": state["chat_history"]
        })
        plan = json.loads(response.content).get("plan", [])
        return {"plan": plan}

    def executor_node(self, state: AgentState):
        plan = state["plan"]
        results = tool_executor(plan)
        return {"tool_results": results}

    def generator_node(self, state: AgentState):
        context = f"""
        User's Original Question: {state['input'].query}
        Your Plan: {state['plan']}
        Results of Executing Plan: {[res.dict() if hasattr(res, 'dict') else res for res in state['tool_results']]}

        Based on the plan and the results, provide a clear, concise, and friendly answer to the user's original question.
        Synthesize all information into a single, coherent response.
        """
        response = self.llm.invoke(context)
        return {"response": response.content}

    def run(self, intent: UserIntent, chat_history: List[BaseMessage]):
        inputs = {"input": intent, "chat_history": chat_history}
        final_state = self.graph.invoke(inputs)
        return final_state["response"]
```

#### **File: `src/agents/planner.py`** (Adjusted for Structured Input)

```python
"""Defines the Planner Agent's prompt for the LangGraph workflow."""
from langchain_core.prompts import ChatPromptTemplate

PLANNER_PROMPT = """
You are an expert network operations planner.
Your job is to create a step-by-step plan of tool calls to fulfill a user's request, which has been pre-processed into a structured intent object.

**Structured Intent from NLP Layer:**
{input}

**Conversation History:**
{chat_history}

**Your Task:**
Convert the structured intent into a concrete plan of tool calls.

**Rules:**
1.  Use the `intent` and `entities` from the structured input to create your plan.
2.  Your job is to create the plan, not to second-guess the intent.
3.  Choose the correct tool for each step: `inventory_search`, `run_network_command`, `analyze_logs`.
4.  If the intent requires multiple pieces of information (e.g., live status AND historical logs), create a multi-step plan.

**Example:**
Structured Intent:
{{
  "query": "show interfaces on S1 and check for flaps",
  "intent": "troubleshoot_history",
  "entities": {{ "device_names": ["S1"], "keywords": ["flaps"] }}
}}

Your Plan:
{{
  "plan": [
    {{
      "tool": "run_network_command",
      "args": {{"device_name": "S1", "command": "show ip interface brief"}}
    }},
    {{
      "tool": "analyze_logs",
      "args": {{"query": "interface flaps on device S1"}}
    }}
  ],
  "reasoning": "The user wants to see the current interface status on S1 and check for historical flaps. I will use `run_network_command` for the live status and `analyze_logs` for the history."
}}

Now, create a plan for the provided structured intent.
"""

def get_planner_prompt():
    """Creates the planner agent prompt component."""
    return ChatPromptTemplate.from_template(PLANNER_PROMPT)
```

#### **File: `main.py`** (The Final Orchestrator)

```python
"""Main entry point for the AI Network Agent V3."""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from src.graph.workflow import NetworkWorkflow
from src.nlp.preprocessor import NLPPreprocessor
from src.tools.inventory import network_manager

def main():
    """Initializes and runs the NLP-First multi-agent network co-pilot."""
    load_dotenv()
    print("🤖 AI Network Agent V3 - NLP-First Co-pilot")
    print("=" * 60)

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("⚠️ GROQ_API_KEY not set! Please create a .env file with your key.")
        return

    if not Path("inventory.yaml").exists():
        print("⚠️ Inventory file 'inventory.yaml' not found. Please create one.")
        return
    print(f"📦 Inventory loaded: {len(network_manager.devices)} devices found.")

    if not Path("./chroma_db").exists():
        print("⚠️ Syslog vector database not found. Run 'python scripts/ingest_logs.py' to create it.")

    try:
        nlp_processor = NLPPreprocessor()
        workflow = NetworkWorkflow(api_key=groq_api_key)
        print("✅ NLP layer and Agent workflow initialized successfully.")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return

    print("\n💡 Ask complex questions like 'show interfaces on S1 and check for recent flaps'")
    print("   Type 'quit' or 'exit' to end the session.")
    print("=" * 60)

    chat_history = []
    while True:
        try:
            question = input("\n💬 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not question:
            continue
        if question.lower() in ["quit", "exit"]:
            break

        print("-" * 40)
        try:
            # 1. NLP Pre-processing
            structured_intent = nlp_processor.process(question)
            print(f"🔍 Intent: {structured_intent.intent} | Entities: {structured_intent.entities.dict(exclude_none=True)}")

            # 2. Intelligent Routing
            if structured_intent.is_ambiguous:
                response = "I'm sorry, your request is a bit ambiguous. Could you please provide more details, like a specific device name?"
            elif structured_intent.intent == "greeting":
                response = "Hello! How can I help you with the network today?"
            elif structured_intent.intent == "unknown":
                response = "I'm not sure how to handle that request. Please try rephrasing."
            else:
                # 3. Execute Agentic Workflow
                response = workflow.run(structured_intent, chat_history)

            print(f"\n🤖 Agent: {response}")
            chat_history.append(HumanMessage(content=question))
            chat_history.append(AIMessage(content=response))
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
        print("-" * 40)

    network_manager.close_all_sessions()
    print("\n👋 All network sessions closed. Goodbye!")

if __name__ == "__main__":
    main()
```

*(Note: The other files like `src/core/network_manager.py`, `src/tools/*`, `src/agents/executor.py`, and `scripts/ingest_logs.py` can be used as they were in Version 2, as their interfaces are stable and they are correctly integrated here.)*
