# AI Network Agent - Simplified 3-Tool Architecture

This is a simplified network automation agent that uses a 3-tool architecture for maximum reliability and maintainability.

## Architecture Overview

The application follows a clean, simplified architecture with only 3 tools:

### Tools
1. **inventory.py** - Handles device listing and searching
2. **executor.py** - Main pipeline for executing network commands
3. **parser.py** - Parses and formats CLI output

### Core Modules
- **inventory.py** - Manages network device inventory from YAML file
- **device_manager.py** - Handles device connections and sessions
- **command_executor.py** - Executes commands on network devices
- **validation.py** - Validates and sanitizes network commands
- **device_router.py** - Routes queries to appropriate devices
- **sensitive_data.py** - Sanitizes sensitive information from output

### Agent
- **main_agent.py** - Single agent that orchestrates the 3 tools

## Features

- Natural language interface for network device management
- Device inventory management from YAML file
- Safe command validation and execution
- Sensitive data sanitization
- Multi-device support

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
 │    ├ device_manager.py
 │    ├ command_executor.py
 │    ├ validation.py
 │    ├ device_router.py
 │    └ sensitive_data.py
 ├ inventory.yaml
 └ main.py
```

## Prerequisites

- Python 3.12+
- uv package manager
- GROQ API key
- Network devices accessible via SSH/TELNET