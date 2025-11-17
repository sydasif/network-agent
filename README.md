# AI Network Agent - Simplified 3-Tool Architecture

This is a simplified network automation agent that uses a 3-tool architecture with a consolidated device management system for maximum reliability and maintainability.

## Architecture Overview

The application follows a clean, simplified architecture with only 3 tools and a consolidated core module:

### Tools

1. **inventory.py** - Handles device listing and searching
2. **executor.py** - Main pipeline for executing network commands
3. **parser.py** - Parses and formats CLI output

### Core Module

- **network_manager.py** - Consolidated network management (replaces multiple modules)
  - Device inventory loading from YAML file
  - Connection/session management
  - Command execution
  - Security validation (dangerous command detection)
  - Output sanitization

### Agent

- **main_agent.py** - Single agent that orchestrates the 3 tools

## Features

- Natural language interface for network device management
- Device inventory management from YAML file
- Safe command validation and execution
- Sensitive data sanitization
- Multi-device support
- Simplified architecture with reduced complexity

## Setup

1. Install dependencies with `uv sync`
2. Set up your `inventory.yaml` file with device information
3. Set your GROQ_API_KEY environment variable
4. Run with `python main.py`

## Usage

Once started, you can ask questions like:

- "show version on S1"
- "list all devices"
- "show interfaces on S2"

## File Structure

```
src/
 ├ tools/
 │    ├ inventory.py
 │    ├ executor.py
 │    └ parser.py
 ├ agent/
 │    └ main_agent.py
 ├ core/
 │    └ network_manager.py (consolidated functionality)
 ├ inventory.yaml
 └ main.py
```

## Simplification Benefits

- **Reduced complexity**: Single NetworkManager class consolidates functionality
- **Easier maintenance**: Fewer files and components to maintain
- **More predictable behavior**: Explicit device and command parameters
- **Same security**: All dangerous command detection and output sanitization preserved
- **Cleaner code**: Removed unnecessary layers of abstraction

## Prerequisites

- Python 3.12+
- uv package manager
- GROQ API key
- Network devices accessible via SSH/TELNET
