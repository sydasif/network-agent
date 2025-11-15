# AI Network Agent - Natural Language Network Automation

Talk to your network devices using natural language! An AI-powered agent that understands your questions, executes the right commands, and provides intelligent summaries.

## 🎯 What It Does

Instead of manually running commands and parsing outputs, simply ask:

```text
💬 "Show me all interfaces and their status"
💬 "What's the device uptime?"
💬 "Which interfaces have errors?"
```

The AI agent will:

1. Understand your question
2. Decide which commands to run
3. Execute them on your device
4. Analyze and summarize the results
5. Give you a clear, concise answer

## ✨ Key Features

- **Natural Language Interface** — Ask questions in plain English
- **Intelligent Command Execution** — AI decides which commands to run
- **Automated Analysis** — Parses and summarizes device output
- **Modular Architecture** — Clean, maintainable code structure
- **Easy Setup** — Works with Cisco devices via SSH
- **Free AI** — Uses Groq's free Llama inference

## 📋 Prerequisites

- Python 3.12+
- `uv` package manager (optional but recommended)
- Groq API key (free at <https://console.groq.com/keys>)
- Network device with SSH access (Cisco IOS)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/sydasif/network-agent.git
cd network-agent
```

### 2. Install Dependencies

```bash
uv sync
# or: pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here
DEVICE_PASSWORD=your_device_password  # Optional
```

**Configuration Variables:**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | ✅ Yes | Free API key from Groq | `gsk_abc123...` |
| `DEVICE_PASSWORD` | ❌ Optional | Device SSH password (prompted if not set) | `MyPassword123` |

**Getting Groq API Key:**

1. Visit <https://console.groq.com/keys>
2. Sign up (free account)
3. Create new API key
4. Copy to `.env` file

**Alternative: Set Environment Variables (Linux/Mac):**

```bash
export GROQ_API_KEY="your_key_here"
export DEVICE_PASSWORD="your_password"
uv run main.py
```

**For Windows (PowerShell):**

```powershell
$env:GROQ_API_KEY="your_key_here"
$env:DEVICE_PASSWORD="your_password"
uv run main.py
```

### 4. Run

```bash
uv run main.py
```

### 5. Configure Settings (Interactive Menu)

Once running, you can customize the agent behavior:

```bash
💬 Ask: /settings

============================================================
Settings Menu
============================================================

1. Model Selection
   Current: openai/gpt-oss-120b
   Options:
   - openai/gpt-oss-120b (recommended - best for networking)
   - llama-3.3-70b-versatile
   - llama-3.1-8b-instant

2. Temperature
   Current: 0.1 (more deterministic)
   Range: 0.0 (deterministic) to 1.0 (creative)

3. Platform Type
   Current: Cisco IOS
   Options: Cisco IOS, Cisco NX-OS, Cisco IOS-XR

4. Verbose Mode
   Current: OFF
   Options: ON/OFF (detailed logging)

5. API Timeout
   Current: 60 seconds
   Range: 10-300 seconds

6. Return to Main Menu
```

**Configuration Options Explained:**

| Setting | Effect | Recommendation |
|---------|--------|-----------------|
| **Model** | Speed & accuracy trade-off | Use `llama-3.3-70b` for best results |
| **Temperature** | Response creativity vs consistency | 0.1 for networking tasks (predictable) |
| **Platform** | Device-specific command formatting | Match your device type |
| **Verbose** | Debug logging for troubleshooting | OFF normally, ON for debugging |
| **Timeout** | Max wait for API response (seconds) | 60 for most cases, 120 for complex queries |

## 📁 Project Structure

```bash
network-agent/
├── main.py                 # Entry point
├── src/                    # Application modules
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── config_file.py     # Configuration file support
│   ├── network_device.py  # Device connection
│   ├── agent.py           # AI agent setup
│   ├── interface.py       # User interface
│   ├── health.py          # Health check functionality
│   ├── metrics.py         # Metrics dashboard
│   └── utils.py           # Utilities
├── config.yaml             # Configuration file example
├── pyproject.toml         # Project dependencies
├── .env                   # Environment secrets
├── tests/                 # Test files
└── README.md              # This file
```

## 🏥 Health Monitoring & Configuration

The application includes comprehensive monitoring capabilities with both health checks and detailed metrics tracking:

### Configuration File Support (`config.yaml`)

The application supports configuration through a YAML file with the following sections:

```yaml
security:
  max_query_length: 500
  max_queries_per_session: 100
  allowed_commands:
    - show
    - display
    - get
  blocked_keywords:
    - reload
    - write
    - configure

logging:
  enable_console: false
  enable_file: true
  enable_json: true
  log_level: INFO

connection:
  max_reconnect_attempts: 3
  connection_timeout: 30
  read_timeout: 60
```

### Health Check Module (`src/health.py`)

- **Health Status Class** — Provides detailed system health information
- **Connection Monitoring** — Tracks device connection state and uptime
- **Agent Status** — Monitors AI agent activity and model usage
- **Command Statistics** — Tracks successful/failed command execution rates
- **System Metrics** — General system information and version

### Health Check Functions

```python
from src.health import health_check, is_system_healthy

# Get detailed health status
health_status = health_check(device, agent, audit_logger)

# Check if system is healthy (boolean)
is_healthy = is_system_healthy(device, agent)
```

### Example Health Check Output

```json
{
  "timestamp": "2025-11-15T13:30:00.123456",
  "connection": {
    "state": "connected",
    "alive": true,
    "connected": true,
    "connection_attempts": 1,
    "uptime_seconds": 3600
  },
  "agent": {
    "model": "llama-3.3-70b-versatile",
    "active": true,
    "model_fallback_count": 0,
    "rate_limit_used": 5,
    "rate_limit_remaining": 25
  },
  "commands": {
    "total": 15,
    "successful": 14,
    "failed": 1,
    "success_rate": 0.93
  },
  "system": {
    "health_check_time": 1731870600.123,
    "version": "1.0.0",
    "status": "healthy"
  }
}
```

### Metrics Dashboard (`src/metrics.py`)

- **Metrics Collection** — Tracks command execution, security events, connections, and model usage
- **Real-time Metrics** — Monitor commands per minute, success rates, and error counts
- **Alert System** — Automatic alerts for low success rates, high security events, and other issues
- **Time-based Analysis** — Historical metrics for trend analysis
- **API Integration** — Web endpoints for monitoring systems

### Metrics Collection Examples

```python
from src.metrics import MetricsCollector, MetricType

# Initialize collector
collector = MetricsCollector(max_events=10000)

# Record different types of events
collector.record_event(MetricType.COMMAND_EXECUTED, {"command": "show version", "output_length": 150})
collector.record_event(MetricType.COMMAND_FAILED, {"command": "invalid command", "error": "syntax error"})
collector.record_event(MetricType.PROMPT_INJECTION_ATTEMPT, {"query": "ignore instructions"})
```

### Metrics Dashboard Functions

```python
from src.metrics import MetricsDashboard

# Create dashboard from collector
dashboard = MetricsDashboard(collector)

# Generate text report
text_report = dashboard.generate_text_report()

# Generate JSON report for APIs
json_report = dashboard.generate_json_report()

# Get alerts based on thresholds
alerts = dashboard.get_alerts()
```

### Web API Integration

The application includes example Flask endpoints demonstrating how to integrate health checks and metrics into a web API:

- **`/health`** — Returns detailed health status with appropriate HTTP status codes
- **`/ready`** — Simple readiness check for container orchestration
- **`/metrics`** — JSON metrics endpoint for monitoring systems
- **`/metrics/text`** — Human-readable metrics output
- **`/metrics/health`** — Health-focused metrics with status

For production deployments, these endpoints can be integrated with monitoring systems, load balancers, and orchestration platforms to ensure service availability and automatically handle failures.

## 🏗️ Architecture

### Modules

| Module | Class | Responsibility |
|--------|-------|-----------------|
| `config.py` | `ConfigManager` | Load environment variables and credentials |
| `config_file.py` | `ConfigManager` | Load configuration from YAML files |
| `network_device.py` | `DeviceConnection` | SSH connection and command execution |
| `agent.py` | `Agent` | LLM setup and AI reasoning |
| `interface.py` | `UserInterface` | Interactive CLI interface |
| `health.py` | `HealthStatus` | System health monitoring |
| `metrics.py` | `MetricsCollector` | Metrics collection and dashboard |
| `utils.py` | — | Formatting and utility functions |

### Data Flow

```text
User Input
    ↓
UserInterface (src/interface.py)
    ├─ Prompts for device credentials
    ├─ Gets Groq API key
    └─ Runs interactive session
        ↓
    Agent (src/agent.py)
    ├─ Receives user question
    ├─ LLM thinks about which commands to run
    └─ Executes via DeviceConnection
        ↓
    DeviceConnection (src/network_device.py)
    └─ Connects via Netmiko SSH
        ↓
    Network Device (Cisco Router/Switch)
    └─ Returns command output
        ↓
    Agent (analyzes output)
    └─ LLM generates human-readable response
        ↓
    UserInterface (displays result)
```

## 💬 Example Usage

```bash
$ uv run main.py

============================================================
AI Network Agent
============================================================

Device IP: 192.168.1.1
Username: admin
Password: ****
✓ Connected to 192.168.1.1

============================================================
Ready! Type 'quit' to exit
============================================================

💬 Ask: Show me all interfaces

------------------------------------------------------------
I found 4 interfaces on your device:

1. **GigabitEthernet0/0** - UP (192.168.1.1)
2. **GigabitEthernet0/1** - UP (10.1.0.1)
3. **GigabitEthernet0/2** - DOWN
4. **Loopback0** - UP (10.0.0.1)
------------------------------------------------------------

💬 Ask: What's the device uptime?

------------------------------------------------------------
The device has been running for:
- 2 days
- 4 hours
- 30 minutes
------------------------------------------------------------

💬 Ask: quit
✓ Disconnected
```

## 🎓 Example Queries

### Device Information

- "What version is running?"
- "What's the hostname?"
- "Show me the uptime"
- "What's the serial number?"

### Interface Management

- "List all interfaces"
- "Which interfaces are down?"
- "Show me interface errors"
- "What's the status of GigabitEthernet0/1?"
- "Show me interface bandwidth utilization"

### Routing

- "Show me the routing table"
- "What's the default gateway?"
- "Show me all static routes"
- "Are there any BGP neighbors?"

### Troubleshooting

- "Are there any errors in the logs?"
- "Show me interface errors"
- "Is there any packet loss?"
- "Show me devices with high CPU"

## 🔧 Technical Stack

### Core Dependencies

- **Netmiko** (4.6.0+) — SSH device connection and command execution
- **LangChain** (0.3.0+) — Modern AI framework and agent orchestration with improved type hints
- **LangGraph** (1.0.3+) — Graph-based agent runtime with ReAct pattern and recursion limits
- **Groq** (0.33+) — LLM API client with rate limiting (30 req/60s)
- **python-dotenv** (1.2+) — Environment variable management

### Models

- **GPT-OSS 120B** (via Groq) — Best for networking tasks (500 tps, 120B parameters)
  - 65K context window for large command outputs
  - Excellent reasoning for network troubleshooting
  - **Recommended for production**

**Alternative models:**

- **Llama 3.3 70B** — High quality, good balance
- **Llama 3.1 8B** — Fast & economical for simple queries

### Python Version

- Python 3.12+ (uses modern type hints, TypedDict, and async/await patterns)

## 🔒 Security Features

This application implements **5 layers of security** to ensure safe, production-ready network automation:

### **Read-Only by Design** 🔒

- Only `show`, `display`, and `get` commands are allowed
- Dangerous commands like `reload`, `write`, `configure` are blocked
- Command validation with whitelist + blacklist protection
- Command chaining protection (blocks `;`, allows safe pipes only)

### **Prompt Injection Defense** 🛡️

- Length limits (500 characters maximum)
- Suspicious pattern detection and blocking
- Query sanitization for malicious content
- Special character limits and validation

### **Sensitive Data Protection** 🔐

- Password/API key automatic sanitization
- SNMP community string redaction
- TACACS/RADIUS secret masking
- Error message sanitization to prevent data leaks

### **Comprehensive Audit Logging** 📝

- Persistent log files (text + JSON format)
- Security event tracking
- Session summaries for compliance
- Structured logging for SIEM integration

### **Thread-Safe Connection Management** 🔌

- Auto-reconnect with exponential backoff
- Connection liveness checking
- Thread-safe operations (no race conditions)
- Proper error messages and state tracking

### **Security Implementation Details**:

1. **Command Validation** — All commands pass through a validation layer that verifies they're on the allowed list and don't contain dangerous keywords
2. **Input Sanitization** — User queries are sanitized before being sent to the LLM to prevent injection attacks
3. **Sensitive Data Redaction** — All logs and outputs automatically redact sensitive information like passwords, API keys, and secrets
4. **Connection Security** — SSH connections are managed with proper error handling and reconnection logic
5. **Rate Limiting Protection** — API usage is monitored and protected against abuse

### **Example `.gitignore`

```bash
.env
.venv/
__pycache__/
*.pyc
.DS_Store
```

## 🔄 Model Fallback System

The agent automatically handles rate limiting and API errors by switching between models:

**Fallback Chain (in priority order):**

1. **openai/gpt-oss-120b** (Primary) — Best for networking, 120B parameters
2. **llama-3.3-70b-versatile** (Fallback 1) — High quality alternative, 70B parameters
3. **llama-3.1-8b-instant** (Fallback 2) — Fast & economical, 8B parameters

**How it works:**

```text
User Query
    ↓
Try Primary Model (openai/gpt-oss-120b)
    ├─ Success? → Return response
    ├─ Rate Limit? → Wait 2s, Switch to Fallback 1
    └─ Timeout? → Wait 1s, Switch to Fallback 1
        ↓
Try Fallback 1 (llama-3.3-70b-versatile)
    ├─ Success? → Return response
    ├─ Rate Limit? → Wait 2s, Switch to Fallback 2
    └─ Timeout? → Wait 1s, Switch to Fallback 2
        ↓
Try Fallback 2 (llama-3.1-8b-instant)
    ├─ Success? → Return response
    └─ Failure? → Return error message
```

**Tracking Model Usage:**

Use `/stats` command to see which models were used:

```bash
💬 Ask: /stats

📊 Session Statistics:
   Total commands: 5
   Successful: 5
   Failed: 0
   Rate limit status: 3/30
   Rate limit active: false

🤖 Model Information:
   Primary model: openai/gpt-oss-120b
   Current model: llama-3.3-70b-versatile
   Fallbacks used: 1
   Model usage:
      - openai/gpt-oss-120b: 3 requests
      - llama-3.3-70b-versatile: 2 requests
```

**Retry Strategy:**

- **Rate Limit Error** → Wait 2 seconds, try next model
- **Timeout Error** → Wait 1 second, try next model
- **Other Errors** → Return error message immediately

## 🎯 Rate Limiting

### Connection Timeout

```bash
Error: Connection timeout
```

**Solution:**

- Verify device IP address: `ping 192.168.1.1`
- Check SSH is enabled on device
- Verify firewall allows SSH (port 22)
- Test SSH manually: `ssh admin@192.168.1.1`

### Authentication Failed

```bash
Error: Authentication failed
```

**Solution:**

- Verify username and password are correct
- Check user has SSH access privilege
- Ensure `.env` file has correct credentials
- Try SSH manually first to debug

### API Rate Limit

```bash
Error: Rate limit exceeded
```

**Solution:**

- Groq free tier: 30 requests/minute
- Wait between queries
- Consider upgrading to paid tier for production use

### Command Not Recognized

```bash
Error: Invalid command
```

**Solution:**

- Verify device OS (IOS vs NX-OS commands differ)
- Try command manually on device first
- Check device capabilities
- Some devices need privilege level

## 📈 Recent Enhancements (v0.1.0)

✅ **Completed in Latest Update:**

- [x] Type hints on all methods for IDE autocomplete
- [x] AgentState TypedDict for type-safe state management
- [x] Recursion limits (max 8 tool calls) preventing infinite loops
- [x] Improved statistics tracking (successful/failed commands, rate limits)
- [x] Proper message extraction with explicit type checking
- [x] Enhanced error handling (GraphRecursionError, TimeoutError, rate limiting)
- [x] Thread-based agent state persistence
- [x] Special commands: `/cmd`, `/stats`, `/history`, `/help`, `/quit`

## 📋 Planned Enhancements (Priority 3 - Optional)

Potential improvements:

- [ ] Graph visualization - `agent.get_graph().draw_mermaid()` for debugging
- [ ] Async support - `answer_question_async()` for parallel device operations
- [ ] Streaming responses - Real-time feedback for long operations
- [ ] Support multiple device types (NX-OS, IOS-XR, ASA)
- [ ] Configuration change capabilities (with safety constraints)
- [ ] Multi-device management and queries
- [ ] Web UI dashboard
- [ ] Scheduled automated health checks
- [ ] Alert notifications and reporting
- [ ] Custom system prompts per device type
- [ ] Integration with monitoring systems

## 🤝 Contributing

This is a modular, extensible codebase. Contributions welcome for:

- Adding support for more device types
- Improving LLM prompts and accuracy
- Adding new tools and capabilities
- Enhanced error handling
- Performance optimizations
- Documentation improvements

## 💡 How It Works

### The Agent Flow

1. **Understanding** — LLM interprets user's natural language question
2. **Planning** — LLM decides which network commands to execute
3. **Execution** — Netmiko runs commands on the device via SSH
4. **Analysis** — LLM analyzes raw command output
5. **Response** — LLM generates a clear, human-readable answer

### Example Flow

```text
User: "Which interfaces have errors?"
  ↓
Agent: "I should run 'show interfaces' and 'show interfaces status'"
  ↓
Execution: SSH runs both commands
  ↓
Output: Raw Cisco CLI output
  ↓
Analysis: LLM parses for error counts
  ↓
Response: "Interface Gi0/1 has 15 input errors and 2 output errors"
```

## 🚀 Performance

- **Response Time**: 2-5 seconds (including SSH + LLM inference)
- **Groq Latency**: ~500ms for free tier
- **SSH Connection**: ~1 second
- **Command Execution**: ~1-2 seconds typical

## 📜 License

MIT License - See LICENSE file for details

## 🆘 Getting Help

1. **Start Simple** — Test with basic `show` commands first
2. **Debug SSH** — Verify you can SSH manually before using agent
3. **Check Credentials** — Ensure `.env` has correct API key and device password
4. **Review Logs** — Error messages indicate what went wrong
5. **Refer to blog.md** — Detailed explanation of architecture

## 🎯 Use Cases

- **Network Troubleshooting** — Quick diagnostics without CLI hunting
- **Health Checks** — Regular device status verification
- **Training** — Learn networking concepts interactively
- **Automation** — Integrate into larger automation workflows
- **Documentation** — AI-generated device reports

## ✅ What's Supported

- ✅ Cisco IOS devices (routers and switches)
- ✅ SSH connections with username/password
- ✅ Show commands (read-only)
- ✅ Natural language queries
- ✅ Command output analysis and summarization
- ✅ Error handling and user feedback

## ❌ What's Not Supported

- ❌ Configuration changes (by design - safety first)
- ❌ Non-Cisco devices (yet)
- ❌ Telnet connections (SSH only)
- ❌ Public key authentication (username/password for now)

---

**Happy Automating!** 🚀🤖
