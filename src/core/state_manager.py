"""Manages the agent's persistent state using a SQLite database.

This module implements the StateManager class which handles the storage and retrieval
of device state snapshots. It provides functionality to save and retrieve network
device states over time, enabling the Proactive Analyzer to detect changes.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional
from contextlib import contextmanager
from src.core.config import settings


class StateManager:
    """Manages persistent storage of device state snapshots using SQLite.

    The StateManager provides methods to save and retrieve device state snapshots,
    allowing the system to track changes over time. It stores command outputs and
    their timestamps in a SQLite database for later analysis.

    Attributes:
        db_path (str): Path to the SQLite database file.
    """

    def __init__(self, db_path: str = settings.state_database_file):
        """Initializes the StateManager.

        Args:
            db_path (str): Path to the SQLite database file. Uses default if None.
        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initializes the SQLite database with the required table structure.

        Creates the 'device_snapshots' table if it doesn't already exist.
        The table stores timestamps, device names, commands, and the resulting data.
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.commit()

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections.

        Ensures that database connections are properly closed even if an exception occurs.
        This prevents connection leaks and handles proper cleanup.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def save_snapshot(self, device_name: str, command: str, data: dict):
        """Saves a device state snapshot to the database.

        Stores the current state data for a specific device and command with a timestamp.

        Args:
            device_name (str): Name of the device being snapshotted.
            command (str): The command that generated the state data.
            data (dict): The state data to store (will be JSON serialized).
        """
        timestamp = datetime.utcnow().isoformat()  # Use UTC timestamp for consistency across systems
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            # Using parameterized queries to prevent SQL injection
            cursor.execute(
                "INSERT INTO device_snapshots (timestamp, device_name, command, data) VALUES (?, ?, ?, ?)",
                (timestamp, device_name, command, json.dumps(data)),
            )
            conn.commit()

    def get_latest_snapshot(self, device_name: str, command: str) -> Optional[dict]:
        """Retrieves the most recent state snapshot for a device and command.

        Fetches the latest stored state for the specified device and command from
        the database. Returns None if no snapshot exists.

        Args:
            device_name (str): Name of the device to retrieve state for.
            command (str): The command that generated the state data.

        Returns:
            Optional[dict]: The most recent state data as a dictionary, or None
            if no snapshot exists for the device and command combination.
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            # Using parameterized queries to prevent SQL injection
            # ORDER BY timestamp DESC LIMIT 1 ensures we get only the most recent snapshot
            cursor.execute(
                "SELECT data FROM device_snapshots WHERE device_name = ? AND command = ? ORDER BY timestamp DESC LIMIT 1",
                (device_name, command),
            )
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
