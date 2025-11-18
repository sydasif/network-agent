"""Health monitoring service that runs continuously to monitor network device health.

This module implements a background service that periodically performs health checks
on network devices, comparing current state with previous snapshots to detect changes.
The service runs as a daemon thread and can be gracefully shut down.
"""

import time
import threading
from typing import Dict, Any
from src.core.network_manager import NetworkManager
from src.agents.analyzer import ProactiveAnalyzer
from src.core.config import settings
from src.core.state_manager import StateManager


class HealthMonitor:
    """Background service for continuous health monitoring of network devices.

    This service runs in a separate thread, periodically checking device health
    and analyzing changes using the ProactiveAnalyzer. It can be started and
    stopped gracefully.
    """

    def __init__(self, api_key: str):
        """Initializes the health monitor with required components.

        Args:
            api_key (str): The Groq API key for the analyzer
        """
        self.health_running = True
        self.network_manager = NetworkManager(settings.inventory_file)
        self.analyzer = ProactiveAnalyzer(api_key=api_key)
        self.state_manager = StateManager()

        # Define default health checks since we removed command.yaml
        self.health_checks = [
            {"command": "show version", "description": "Device version and status"},
            {"command": "show interfaces", "description": "Interface status and statistics"},
            {"command": "show ip route", "description": "Routing table information"},
            {"command": "show processes cpu", "description": "CPU utilization"},
            {"command": "show memory", "description": "Memory utilization"}
        ]

    def start_monitoring(self, interval: int = 900):  # Default to 15 minutes
        """Starts the health monitoring service in a background thread.

        Args:
            interval (int): Interval between health checks in seconds (default: 900s = 15min)
        """
        monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        monitor_thread.start()
        print(f"✅ Health monitor started, checking every {interval} seconds")

    def _monitor_loop(self, interval: int):
        """Main monitoring loop that runs in the background thread.

        Args:
            interval (int): Interval between health checks in seconds
        """
        print("🔄 Health monitoring started...")
        while self.health_running:
            try:
                self._perform_health_checks()
                # Wait for the specified interval before next check, but check health_running periodically
                for _ in range(interval):
                    if not self.health_running:
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                print("⚠️ Health monitor interrupted")
                break
            except Exception as e:
                print(f"⚠️ Error in health monitor: {e}")
                # Wait before retrying to avoid rapid error loops
                time.sleep(min(60, interval))  # Wait at least 60s or the interval if smaller

        print("🛑 Health monitor stopped")

    def _perform_health_checks(self):
        """Performs health checks on all devices."""
        for device in self.network_manager.devices.values():
            for check in self.health_checks:
                command = check["command"]
                try:
                    current_output = self.network_manager.execute_command(device.name, command)
                    current_state = {"output": current_output}

                    # Use the analyzer's built-in snapshot storage functionality
                    analysis = self.analyzer.analyze_with_snapshot_storage(device.name, command, current_state)
                    significance = analysis['significance']
                    summary = analysis['summary']
                    print(f"📊 [{time.strftime('%H:%M:%S')}] {device.name} - '{command}': [{significance}] {summary}")

                except Exception as e:
                    print(f"❌ [{time.strftime('%H:%M:%S')}] Error checking {device.name} with '{command}': {e}")

    def stop_monitoring(self):
        """Stops the health monitoring service gracefully."""
        print("🛑 Stopping health monitor...")
        self.health_running = False
        # Close network connections
        self.network_manager.close_all_sessions()
        print("✅ Health monitor stopped")