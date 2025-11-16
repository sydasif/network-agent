"""Session management for network automation."""

import logging

from .audit import AuditLogger, SecurityEventType
from .settings import settings


logger = logging.getLogger("net_agent.session_manager")


class SessionManager:
    """Manage session lifecycle and limits."""
    
    def __init__(self, audit_logger: AuditLogger):
        """Initialize session manager."""
        self.audit_logger = audit_logger
        self.query_count = 0
        self.max_queries_per_session = settings.max_queries_per_session
    
    def increment_query_count(self):
        """Increment the query counter."""
        self.query_count += 1
    
    def is_session_limit_reached(self) -> bool:
        """Check if session limit has been reached."""
        return self.query_count >= self.max_queries_per_session
    
    def get_query_count(self) -> int:
        """Get current query count."""
        return self.query_count
    
    def reset(self):
        """Reset session state."""
        self.query_count = 0
    
    def start_session(self, user: str = "network_admin", device: str = "inventory_based"):
        """Start a new session."""
        self.audit_logger.log_session_start(
            user=user,
            device=device,
            model=settings.model_name,
        )
    
    def end_session(self):
        """End the current session."""
        self.audit_logger.log_session_end()