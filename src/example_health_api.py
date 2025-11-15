"""
Example Flask web application with health check endpoint.

This demonstrates how to integrate the health check functionality
into a web framework. This is for demonstration purposes only.
"""

from flask import Flask, jsonify
import sys
import os

# Add src to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.health import health_check, is_system_healthy
# In a real implementation, you would have your device and agent instances
# For this example, we'll show the structure

app = Flask(__name__)

# In a real application, these would be initialized properly
# device = DeviceConnection()
# agent = Agent(...)
# audit_logger = AuditLogger(...)

@app.route('/health', methods=['GET'])
def health_endpoint():
    """Health check endpoint that returns system health status."""
    # In a real implementation, you would have actual device and agent instances
    # For demonstration, we'll create dummy objects that match the expected interface
    from unittest.mock import Mock
    from src.network_device import DeviceConnection
    from src.agent import Agent
    
    mock_device = Mock(spec=DeviceConnection)
    mock_device.get_connection_status.return_value = {
        "state": "connected",
        "is_alive": True,
        "connected": True,
        "uptime_seconds": 3600
    }
    
    mock_agent = Mock(spec=Agent)
    mock_agent.current_model = "llama-3.3-70b-versatile"
    mock_agent.is_active = True
    mock_agent.total_commands = 15
    mock_agent.successful_commands = 14
    mock_agent.model_fallback_count = 1
    mock_agent.rate_limit_used = 3
    
    # Get health status
    health_status = health_check(mock_device, mock_agent)
    
    # Determine HTTP status code based on system health
    is_healthy = is_system_healthy(mock_device, mock_agent)
    
    # Return appropriate HTTP status
    status_code = 200 if is_healthy else 503
    
    return jsonify(health_status), status_code


@app.route('/ready', methods=['GET'])
def readiness_endpoint():
    """Readiness check endpoint for container orchestration."""
    # Similar to health but might check more specific readiness indicators
    from unittest.mock import Mock
    from src.network_device import DeviceConnection
    from src.agent import Agent
    
    mock_device = Mock(spec=DeviceConnection)
    mock_device.get_connection_status.return_value = {
        "state": "connected",
        "is_alive": True,
        "connected": True,
        "uptime_seconds": 3600
    }
    
    mock_agent = Mock(spec=Agent)
    mock_agent.current_model = "llama-3.3-70b-versatile"
    mock_agent.is_active = True
    mock_agent.total_commands = 15
    mock_agent.successful_commands = 14
    
    is_ready = is_system_healthy(mock_device, mock_agent)
    
    readiness_status = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": "2025-11-15T13:30:00Z"
    }
    
    status_code = 200 if is_ready else 503
    
    return jsonify(readiness_status), status_code


if __name__ == '__main__':
    print("Starting Flask health check example server...")
    print("Visit http://localhost:5000/health for health status")
    print("Visit http://localhost:5000/ready for readiness status")
    app.run(debug=True, host='0.0.0.0', port=5000)