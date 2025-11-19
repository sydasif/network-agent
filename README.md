# AI Network Agent

AI Network Agent is a command-line interface tool that allows network administrators to interact with network devices using natural language commands. The system leverages a Large Language Model (LLM) to interpret user requests and execute appropriate commands on network devices.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [FAQ](#faq)

## Features

- Interpret natural language commands for network devices
- Execute commands on multiple network devices simultaneously
- Interactive chat interface for real-time interaction
- Support for various network device platforms
- Secure credential management

## Prerequisites

- Python 3.12 or higher
- [GROQ API key](https://console.groq.com/) for LLM processing
- Network devices accessible via SSH
- Git for version control

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd net-agent
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Activate the virtual environment:
```bash
source .venv/bin/activate
```

## Configuration

1. Create a `.env` file in the project root:
```bash
GROQ_API_KEY=your_groq_api_key_here
```

2. Configure your network inventory in the `inventory/` directory:
   - `hosts.yaml`: Define your network devices
   - `groups.yaml`: Group devices by function or location
   - `defaults.yaml`: Set default credentials and platform settings

Example `inventory/hosts.yaml`:
```yaml
---
R1:
  hostname: 192.168.121.101

R2:
  hostname: 192.168.121.102

S1:
  hostname: 192.168.121.103

S2:
  hostname: 192.168.121.104
```

Example `inventory/defaults.yaml`:
```yaml
---
username: admin
password: admin
platform: cisco_ios
connection_options:
  netmiko:
    timeout: 10
```

## Usage

Start the interactive chat session:
```bash
uv run main.py chat
```

Example commands you can use:
- "Show interfaces on R1"
- "Display IP configuration on S1"
- "Check routing table on R2"
- "Show version on all devices"

To exit the chat session, type "quit" or "exit".

## API Reference

### Main Module (`main.py`)

#### `chat()`
Starts an interactive chat session with the network agent. This function initializes the SimpleNetworkAgent with the GROQ API key, then enters an interactive loop to process user queries. The process involves LLM-based interpretation of natural language requests and execution of appropriate network commands on the specified devices.

### Agent Module (`src/agents/simple_agent.py`)

#### `SimpleNetworkAgent`
A simplified AI agent for network command execution. This agent takes natural language input, determines the appropriate network command to execute, and uses Nornir to execute it on the specified device.

##### `__init__(self, api_key: str)`
Initialize the agent with an LLM instance.

###### Parameters:
- `api_key`: The API key for the Groq LLM service

##### `process_request(self, user_input: str) -> Dict[str, str]`
Process a natural language request and execute the appropriate command.

###### Parameters:
- `user_input`: Natural language request from the user

###### Returns:
- Dictionary with device name, command, and output

##### `close_sessions(self)`
Close all network sessions.

#### `NetworkCommand`
Model for extracted network command information.

### Network Manager Module (`src/core/network_manager.py`)

#### `NetworkManager`
Manages network device connections and command execution using Nornir.

##### `__init__(self, config_file: str = "inventory/config.yaml")`
Initializes the NetworkManager with Nornir.

###### Parameters:
- `config_file` (str): Path to the Nornir configuration file.

##### `get_device_names(self) -> List[str]`
Returns a list of all device names in the inventory.

###### Returns:
- List[str]: List of device names in the inventory.

##### `execute_command(self, device_name: str, command: str) -> str`
Executes a command on a specific device using Nornir.

###### Parameters:
- `device_name` (str): Name of the device to execute the command on.
- `command` (str): The command to execute on the device.

###### Returns:
- str: The output of the executed command.

###### Raises:
- ValueError: If the device is not found in inventory.
- Exception: If command execution fails.

##### `execute_command_on_multiple_devices(self, device_names: List[str], command: str) -> Dict[str, str]`
Executes a command on multiple devices.

###### Parameters:
- `device_names` (List[str]): List of device names to execute the command on.
- `command` (str): The command to execute on the devices.

###### Returns:
- Dict[str, str]: Dictionary mapping device names to command outputs.

##### `close_all_sessions(self)`
Closes all active Nornir sessions.

## Architecture

The system is organized into the following components:

- `main.py`: The entry point for the CLI application, providing an interactive chat interface.
- `src/agents/simple_agent.py`: Contains the AI agent that processes natural language requests and executes commands.
- `src/core/network_manager.py`: Handles network device connections and command execution.
- `src/core/config.py`: Application configuration management using Pydantic Settings.
- `src/core/models.py`: Data models for the application using Pydantic.
- `tests/`: Contains unit tests for the application components.

## FAQ

### How does the AI agent work?
The agent uses a Large Language Model (GROQ API) to interpret natural language commands. It identifies the target device and the command to execute, then uses Nornir to connect to the device and run the command.

### What network devices are supported?
The system supports any network device that is compatible with Netmiko, including most Cisco, Juniper, Arista, and other vendor devices.

### Is my API key secure?
Your GROQ API key is stored in the `.env` file and is not committed to the repository. Ensure proper file permissions are set to protect this file.

### Can I execute commands on multiple devices at once?
Currently, the interactive chat supports commands on a single device. The underlying NetworkManager supports multi-device commands through its API.