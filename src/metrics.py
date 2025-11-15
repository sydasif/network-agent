"""
Metrics dashboard for the network agent.

Provides metrics tracking and reporting for monitoring system performance,
command execution, security events, and connection stability.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import deque, defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    """Types of metrics tracked by the system."""
    COMMAND_EXECUTED = "command_executed"
    COMMAND_FAILED = "command_failed"
    COMMAND_BLOCKED = "command_blocked"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_FAILED = "connection_failed"
    CONNECTION_LOST = "connection_lost"
    PROMPT_INJECTION_ATTEMPT = "prompt_injection_attempt"
    MODEL_FALLBACK = "model_fallback"
    SECURITY_EVENT = "security_event"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass
class MetricEvent:
    """Represents a single metric event."""
    timestamp: float
    metric_type: MetricType
    details: Dict[str, Any]


class MetricsCollector:
    """Collects and stores metrics for the network agent."""

    def __init__(self, max_events: int = 10000):
        """Initialize the metrics collector.

        Args:
            max_events: Maximum number of events to store in memory
        """
        self.max_events = max_events
        self.events = deque(maxlen=max_events)
        self.lock = threading.Lock()
        
        # Counters for different metric types
        self.counters = defaultdict(int)
        self.start_time = time.time()

    def record_event(self, metric_type: MetricType, details: Dict[str, Any] = None):
        """Record a new metric event.

        Args:
            metric_type: Type of metric being recorded
            details: Additional details about the event
        """
        if details is None:
            details = {}

        event = MetricEvent(
            timestamp=time.time(),
            metric_type=metric_type,
            details=details
        )

        with self.lock:
            self.events.append(event)
            self.counters[metric_type] += 1

    def get_total_events(self) -> int:
        """Get the total number of events recorded."""
        with self.lock:
            return len(self.events)

    def get_event_count(self, metric_type: MetricType) -> int:
        """Get the count of a specific type of event.

        Args:
            metric_type: Type of event to count

        Returns:
            Number of events of the specified type
        """
        with self.lock:
            return self.counters[metric_type]

    def get_events_in_time_range(self, start_time: float, end_time: float) -> List[MetricEvent]:
        """Get events within a specific time range.

        Args:
            start_time: Start of time range (timestamp)
            end_time: End of time range (timestamp)

        Returns:
            List of events in the specified time range
        """
        with self.lock:
            return [event for event in self.events if start_time <= event.timestamp <= end_time]

    def get_events_by_type(self, metric_type: MetricType) -> List[MetricEvent]:
        """Get all events of a specific type.

        Args:
            metric_type: Type of events to return

        Returns:
            List of events of the specified type
        """
        with self.lock:
            return [event for event in self.events if event.metric_type == metric_type]

    def get_command_metrics(self) -> Dict[str, Any]:
        """Get command-related metrics.

        Returns:
            Dictionary with command execution metrics
        """
        executed = self.get_event_count(MetricType.COMMAND_EXECUTED)
        failed = self.get_event_count(MetricType.COMMAND_FAILED)
        blocked = self.get_event_count(MetricType.COMMAND_BLOCKED)
        
        total = executed + failed + blocked
        success_rate = executed / total if total > 0 else 0
        
        return {
            "total_commands": total,
            "successful_commands": executed,
            "failed_commands": failed,
            "blocked_commands": blocked,
            "success_rate": success_rate
        }

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security-related metrics.

        Returns:
            Dictionary with security metrics
        """
        injection_attempts = self.get_event_count(MetricType.PROMPT_INJECTION_ATTEMPT)
        blocked_commands = self.get_event_count(MetricType.COMMAND_BLOCKED)
        rate_limit_events = self.get_event_count(MetricType.RATE_LIMIT_EXCEEDED)
        
        return {
            "prompt_injection_attempts": injection_attempts,
            "blocked_commands": blocked_commands,
            "rate_limit_exceeded": rate_limit_events,
            "security_events": injection_attempts + blocked_commands + rate_limit_events
        }

    def get_connection_metrics(self) -> Dict[str, Any]:
        """Get connection-related metrics.

        Returns:
            Dictionary with connection metrics
        """
        established = self.get_event_count(MetricType.CONNECTION_ESTABLISHED)
        failed = self.get_event_count(MetricType.CONNECTION_FAILED)
        lost = self.get_event_count(MetricType.CONNECTION_LOST)
        
        total = established + failed
        success_rate = established / total if total > 0 else 0
        
        return {
            "successful_connections": established,
            "failed_connections": failed,
            "connections_lost": lost,
            "connection_success_rate": success_rate
        }

    def get_model_metrics(self) -> Dict[str, Any]:
        """Get model-related metrics.

        Returns:
            Dictionary with model usage metrics
        """
        fallbacks = self.get_event_count(MetricType.MODEL_FALLBACK)
        
        return {
            "model_fallbacks": fallbacks,
            "total_model_interactions": sum(
                self.get_event_count(mt) for mt in [
                    MetricType.COMMAND_EXECUTED, 
                    MetricType.COMMAND_FAILED,
                    MetricType.MODEL_FALLBACK
                ]
            )
        }

    def get_uptime_seconds(self) -> float:
        """Get the system uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return time.time() - self.start_time

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all metrics.

        Returns:
            Dictionary with comprehensive metrics summary
        """
        uptime_seconds = self.get_uptime_seconds()
        
        return {
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": str(timedelta(seconds=int(uptime_seconds))),
            "total_events": self.get_total_events(),
            "command_metrics": self.get_command_metrics(),
            "security_metrics": self.get_security_metrics(),
            "connection_metrics": self.get_connection_metrics(),
            "model_metrics": self.get_model_metrics(),
            "timestamp": datetime.fromtimestamp(time.time()).isoformat()
        }

    def get_commands_per_minute(self, minutes: int = 1) -> float:
        """Get the average number of commands executed per minute.

        Args:
            minutes: Number of minutes to calculate average over

        Returns:
            Average commands per minute
        """
        now = time.time()
        start_time = now - (minutes * 60)
        
        command_events = [
            event for event in self.get_events_by_type(MetricType.COMMAND_EXECUTED)
            if event.timestamp >= start_time
        ]
        
        return len(command_events) / minutes if minutes > 0 else 0

    def get_recent_security_events(self, minutes: int = 5) -> List[MetricEvent]:
        """Get security-related events from the last specified minutes.

        Args:
            minutes: Number of minutes to look back

        Returns:
            List of recent security events
        """
        now = time.time()
        start_time = now - (minutes * 60)
        
        security_types = {
            MetricType.PROMPT_INJECTION_ATTEMPT,
            MetricType.COMMAND_BLOCKED,
            MetricType.RATE_LIMIT_EXCEEDED,
            MetricType.SECURITY_EVENT
        }
        
        with self.lock:
            return [
                event for event in self.events
                if event.metric_type in security_types and event.timestamp >= start_time
            ]


class MetricsDashboard:
    """Provides a dashboard interface for metrics visualization."""

    def __init__(self, collector: MetricsCollector):
        """Initialize the metrics dashboard.

        Args:
            collector: MetricsCollector instance to use
        """
        self.collector = collector

    def generate_text_report(self) -> str:
        """Generate a text-based metrics report.

        Returns:
            Formatted text report with metrics
        """
        metrics = self.collector.get_metrics_summary()
        
        report = [
            "=" * 60,
            "NETWORK AGENT METRICS DASHBOARD",
            "=" * 60,
            f"Uptime: {metrics['uptime_formatted']}",
            f"Started: {metrics['timestamp']}",
            f"Total Events Tracked: {metrics['total_events']}",
            "",
            "COMMAND EXECUTION:",
            f"  Total Commands: {metrics['command_metrics']['total_commands']}",
            f"  Successful: {metrics['command_metrics']['successful_commands']}",
            f"  Failed: {metrics['command_metrics']['failed_commands']}",
            f"  Blocked: {metrics['command_metrics']['blocked_commands']}",
            f"  Success Rate: {metrics['command_metrics']['success_rate']:.2%}",
            f"  Commands/Minute: {self.collector.get_commands_per_minute():.2f}",
            "",
            "SECURITY EVENTS:",
            f"  Prompt Injection Attempts: {metrics['security_metrics']['prompt_injection_attempts']}",
            f"  Blocked Commands: {metrics['security_metrics']['blocked_commands']}",
            f"  Rate Limit Exceeded: {metrics['security_metrics']['rate_limit_exceeded']}",
            f"  Total Security Events: {metrics['security_metrics']['security_events']}",
            "",
            "CONNECTION STATUS:",
            f"  Successful Connections: {metrics['connection_metrics']['successful_connections']}",
            f"  Failed Connections: {metrics['connection_metrics']['failed_connections']}",
            f"  Connections Lost: {metrics['connection_metrics']['connections_lost']}",
            f"  Connection Success Rate: {metrics['connection_metrics']['connection_success_rate']:.2%}",
            "",
            "MODEL PERFORMANCE:",
            f"  Model Fallbacks: {metrics['model_metrics']['model_fallbacks']}",
            f"  Total Model Interactions: {metrics['model_metrics']['total_model_interactions']}",
            "=" * 60,
        ]
        
        return "\n".join(report)

    def generate_json_report(self) -> Dict[str, Any]:
        """Generate a JSON-formatted metrics report.

        Returns:
            Dictionary with metrics in JSON-compatible format
        """
        return self.collector.get_metrics_summary()

    def get_alerts(self) -> List[str]:
        """Get any alerts based on metrics thresholds.

        Returns:
            List of alert messages
        """
        alerts = []
        metrics = self.collector.get_metrics_summary()
        
        # Check for high command failure rate
        cmd_metrics = metrics['command_metrics']
        if cmd_metrics['total_commands'] > 0 and cmd_metrics['success_rate'] < 0.8:
            alerts.append(
                f"HIGH: Command success rate is low: {cmd_metrics['success_rate']:.2%}"
            )
        
        # Check for high connection failure rate
        conn_metrics = metrics['connection_metrics']
        total_conn = conn_metrics['successful_connections'] + conn_metrics['failed_connections']
        if total_conn > 0 and conn_metrics['connection_success_rate'] < 0.8:
            alerts.append(
                f"HIGH: Connection success rate is low: {conn_metrics['connection_success_rate']:.2%}"
            )
        
        # Check for high security events
        sec_metrics = metrics['security_metrics']
        if sec_metrics['security_events'] > 10:
            alerts.append(
                f"MEDIUM: High number of security events: {sec_metrics['security_events']}"
            )
        
        # Check for model fallbacks
        model_metrics = metrics['model_metrics']
        if model_metrics['model_fallbacks'] > 5:
            alerts.append(
                f"LOW: Multiple model fallbacks occurred: {model_metrics['model_fallbacks']}"
            )
        
        return alerts


# Global metrics collector for application-wide use
# In a real application, this would be initialized once and shared
# global_metrics_collector = MetricsCollector()