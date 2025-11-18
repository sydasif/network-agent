"""Main entry point for the AI Network Agent FastAPI server.

This module starts the FastAPI server for the network agent API. It can be run
directly to start the server or imported as a module.
"""
import uvicorn
import os
from src.core.config import settings


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server.

    Args:
        host (str): Host address to bind the server to
        port (int): Port number to bind the server to
    """
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development only
        log_level="info"
    )


if __name__ == "__main__":
    # Get host and port from environment variables if available
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    print(f"🚀 Starting AI Network Agent API server on {host}:{port}")
    print(f"📖 Inventory file: {settings.inventory_file}")
    print(f"🧠 Groq model: {settings.groq_model_name}")

    start_server(host=host, port=port)