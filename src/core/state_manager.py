"""Manages the agent's persistent state using a SQLite database."""
import sqlite3
import json
from datetime import datetime
from typing import Optional
from src.core.config import settings

class StateManager:
    def __init__(self, db_path: str = settings.state_database_file):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._initialize_db()

    def _initialize_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device_name TEXT NOT NULL,
                command TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def save_snapshot(self, device_name: str, command: str, data: dict):
        timestamp = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO device_snapshots (timestamp, device_name, command, data) VALUES (?, ?, ?, ?)",
            (timestamp, device_name, command, json.dumps(data))
        )
        self.conn.commit()

    def get_latest_snapshot(self, device_name: str, command: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT data FROM device_snapshots WHERE device_name = ? AND command = ? ORDER BY timestamp DESC LIMIT 1",
            (device_name, command)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def close(self):
        self.conn.close()