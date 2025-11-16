# Network Agent API Documentation

This document describes the internal APIs and interfaces provided by the Network Agent.

## Table of Contents

- [Modules Overview](#modules-overview)
- [Agent Module](#agent-module)
- [Network Device Module](#network-device-module)
- [Security Module](#security-module)
- [Audit Module](#audit-module)
- [Sensitive Data Module](#sensitive-data-module)
- [Settings Module](#settings-module)
- [Interface Module](#interface-module)

## Modules Overview

The Network Agent is composed of several interconnected modules:

```
User Interface → Agent → Network Device
     ↓              ↓         ↓
  Security ←———— Audit ←———— Sensitive Data
     ↓
  Settings
```

## Agent Module

### `Agent` Class

The main AI agent that processes user questions and executes commands.

#### Constructor

```python
agent = Agent(
    groq_api_key: str,
    device: DeviceConnection,
    model_name: str,
    temperature: float = 0.1,
    verbose: bool = False,
    timeout: int = 60,
    audit_logger: AuditLogger = None
)
```

**Parameters:**

- `groq_api_key`: Groq API key for LLM access
- `device`: DeviceConnection instance for executing commands
- `model_name`: Name of the LLM model to use
- `temperature`: Controls randomness in responses (0.0-1.0)
- `verbose`: Enable verbose logging
- `timeout`: Request timeout in seconds
- `audit_logger`: Optional audit logger

#### Methods

**`answer_question(question: str) -> str`**

- Process a natural language question
- Execute necessary commands
- Return AI-generated response
- Handles errors and returns appropriate messages

**`_execute_device_command(command: str) -> str`**

- Execute a validated command on the device
- Return command output or error message
- Handles security validation automatically

---

## Network Device Module

### `DeviceConnection` Class

Manages SSH connections and command execution on network devices.

#### Constructor

```python
device = DeviceConnection()
```

#### Methods

**`connect(hostname: str, username: str, password: str)`**

- Establish SSH connection to device
- Raises ConnectionError on failure

**`disconnect()`**

- Close the SSH connection gracefully

**`execute_command(command: str) -> str`**

- Execute a command on the connected device
- Returns command output as string
- Raises ConnectionError on execution failure

**`get_connection_status() -> dict`**

- Returns connection status information:
  - `connected`: Boolean indicating active connection
  - `device`: Device hostname/IP

---

## Security Module

### `CommandSecurityPolicy` Class

Validates commands against security rules.

#### Constructor

```python
policy = CommandSecurityPolicy()
```

#### Methods

**`validate_command(command: str) -> tuple[bool, str]`**

- Validates a command against security policies
- Returns `(is_valid, reason)` tuple
- Checks against blocked keywords and allowed prefixes
- Validates against command chaining patterns

---

## Audit Module

### `AuditLogger` Class

Provides security logging functionality.

#### Constructor

```python
logger = AuditLogger(
    log_dir: str = "logs",
    enable_console: bool = True,
    enable_file: bool = True,
    log_level: str = "INFO"
)
```

**Parameters:**

- `log_dir`: Directory for log files
- `enable_console`: Enable console logging
- `enable_file`: Enable file logging
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

#### Methods

**`log_session_start(user: str, device: str, model: str)`**

- Log session start event

**`log_connection_established(device: str, username: str)`**

- Log successful connection

**`log_connection_failed(device: str, username: str, error: str)`**

- Log connection failure

**`log_command_executed(command: str, success: bool, output_length: int = 0, error: str = None)`**

- Log command execution result

**`log_command_blocked(command: str, reason: str)`**

- Log blocked command attempt

**`close()`**

- Close the logger and finalize session

---

## Sensitive Data Module

### `SensitiveDataProtector` Class

Provides data sanitization and protection.

#### Methods

**`sanitize_for_logging(text: str) -> str`**

- Remove/replace sensitive information from text

**`sanitize_command(command: str) -> str`**

- Sanitize command before logging

**`sanitize_output(output: str, max_length: int = 1000) -> str`**

- Sanitize command output before logging

**`sanitize_error(error: str) -> str`**

- Sanitize error messages

**`mask_password(password: str) -> str`**

- Mask password for display (returns "****" or "*" * len(password))

**`mask_api_key(api_key: str) -> str`**

- Mask API key for display (shows first/last 4 chars)

---

## Settings Module

### `Settings` Class

Centralized configuration using Pydantic.

#### Attributes

**Model Settings:**

- `model_name: str` - LLM model name (default: "llama-3.3-70b-versatile")
- `temperature: float` - LLM temperature (default: 0.1)
- `api_timeout: int` - API timeout in seconds (default: 60)

**Security Settings:**

- `max_query_length: int` - Maximum query length (default: 500)
- `max_queries_per_session: int` - Queries limit (default: 100)
- `allowed_commands: List[str]` - Command prefixes allowed (default: ["show", "display", "get", "dir", "more", "verify"])
- `blocked_keywords: List[str]` - Keywords that block commands

**Logging Settings:**

- `log_level: str` - Default log level (default: "INFO")
- `log_directory: str` - Log directory (default: "logs")
- `enable_console_logging: bool` - Enable console logs (default: True)
- `enable_file_logging: bool` - Enable file logs (default: True)

**Connection Settings:**

- `connection_timeout: int` - Connection timeout (default: 30)
- `read_timeout: int` - Read timeout (default: 60)
- `command_timeout: int` - Command timeout (default: 60)
- `banner_timeout: int` - Banner timeout (default: 15)
- `global_delay_factor: int` - Delay factor (default: 2)

**API Key:**

- `groq_api_key: str` - Required Groq API key

### `settings` Instance

A global instance of Settings that can be imported and used throughout the application:

```python
from src.settings import settings
print(settings.model_name)  # Access settings
```

---

## Interface Module

### `UserInterface` Class

Provides the interactive command-line interface.

#### Constructor

```python
ui = UserInterface()
```

#### Methods

**`run()`**

- Start the interactive session
- Handles device connection and user interaction
- Processes user queries and displays responses

### `InputValidator` Class

Validates and sanitizes user input.

#### Constructor

```python
validator = InputValidator(audit_logger=None, max_query_length: int = 500)
```

#### Methods

**`validate_query(query: str) -> tuple[bool, str]`**

- Validate user query against security constraints
- Returns `(is_valid, error_message)`

**`sanitize_query(query: str) -> str`**

- Sanitize query before LLM processing
- Removes HTML tags, null bytes, and other potential issues

---

## Enums

### `SecurityEventType`

Defined in `src/audit.py`:

- `SESSION_START` - Session begins
- `SESSION_END` - Session ends
- `CONNECTION` - Connection event
- `COMMAND` - Command execution
- `ERROR` - Error event
