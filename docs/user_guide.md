# Network Agent User Guide

This guide provides detailed instructions on how to use the AI Network Agent effectively.

## Table of Contents

- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Security Features](#security-features)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Getting Started

### Prerequisites

- Python 3.12 or higher
- `uv` package manager
- Groq API key (free at [console.groq.com](https://console.groq.com/keys))
- SSH access to a network device (Cisco IOS)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/network-agent.git
   cd network-agent
   ```

2. Create and activate a virtual environment:

   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/macOS
   # OR
   .venv\Scripts\Activate.ps1  # On Windows
   ```

3. Install dependencies:

   ```bash
   uv pip install .
   ```

### First Run

1. Create a `.env` file with your Groq API key:

   ```
   GROQ_API_KEY=your_api_key_here
   ```

2. Run the application:

   ```bash
   uv run main.py
   ```

3. When prompted, enter your device's IP address, username, and password.

## Configuration

### Settings Overview

The application uses a single `settings.py` file for configuration. Key settings include:

- `model_name`: The LLM model to use (default: "llama-3.3-70b-versatile")
- `temperature`: Controls randomness in responses (default: 0.1)
- `max_query_length`: Maximum length of user queries (default: 500)
- `max_queries_per_session`: Limit on queries per session (default: 100)
- `allowed_commands`: List of command prefixes allowed (show, display, get, etc.)
- `blocked_keywords`: Keywords that block command execution

### Environment Variables

- `GROQ_API_KEY`: Required for accessing the LLM
- Other settings can be overridden via environment variables

## Usage Examples

### Common Queries

The agent can interpret various natural language queries:

**Device Information:**

- "What version is running?"
- "What's the device uptime?"
- "Show me the hostname"
- "What's the serial number?"

**Interface Management:**

- "List all interfaces"
- "Which interfaces are down?"
- "Show interface errors"
- "Status of GigabitEthernet0/1"
- "Interface bandwidth utilization"

**Routing:**

- "Show routing table"
- "Default gateway"
- "Static routes"
- "BGP neighbors"

**Security:**

- "Show security features"
- "Access control lists"
- "Security violations"

### How It Works

1. You ask a question in natural language
2. The agent determines the appropriate network commands
3. Commands are validated for security
4. Valid commands are executed on the device
5. Output is analyzed by the AI
6. A human-readable response is generated

## Security Features

### Command Validation

- Only commands starting with allowed prefixes are executed
- Commands containing blocked keywords are rejected
- Command chaining (using `;`) is prevented
- Only safe pipe operations are allowed

### Input Sanitization

- Query length is limited
- Suspicious patterns are detected and blocked
- Special characters are properly handled

### Data Protection

- Sensitive information is automatically redacted from logs
- API keys and passwords are protected
- Audit logs maintain security events

## Troubleshooting

### Common Issues

**Connection Failures:**

- Verify device IP address is correct
- Check network connectivity with `ping`
- Ensure SSH is enabled on the device
- Verify credentials are correct
- Check if firewall is blocking SSH (port 22)

**API Issues:**

- Verify your Groq API key is correct
- Check if you've exceeded API rate limits
- Ensure internet connectivity

**Command Execution Issues:**

- Ensure commands are in the allowed list
- Check that the command doesn't contain blocked keywords
- Verify the device accepts the command syntax

### Error Messages

- **SSH Authentication Failed**: Wrong username/password
- **Connection Timeout**: Device unreachable or SSH not enabled
- **Command Blocked**: Command contained blocked content
- **Rate limit hit**: Wait and try again

### Debugging Tips

1. Test SSH connection manually before using the agent
2. Start with simple `show` commands
3. Check log files in the `logs` directory
4. Verify your API key is valid and not expired

## Best Practices

### Security

- Use read-only accounts when possible
- Regularly audit log files
- Protect API keys appropriately
- Don't store credentials in version control

### Usage

- Start with simple queries to familiarize yourself
- Be specific in your questions
- Use the agent for information gathering, not configuration
- Monitor the commands executed by the agent

### Performance

- The default model is optimized for network tasks
- Complex queries may take longer to process
- Consider the network latency when asking multiple questions

### Maintenance

- Regularly update dependencies
- Review and rotate API keys periodically
- Monitor log files for security events
- Check for application updates

## Support

If you encounter issues:

1. Check the troubleshooting section
2. Review the log files for detailed error information
3. Ensure all prerequisites are met
4. Verify configuration is correct
5. Consider creating an issue in the repository if the problem persists

The agent is designed to be secure and reliable. By following these guidelines, you'll have a better experience using the network agent for your daily operations.
