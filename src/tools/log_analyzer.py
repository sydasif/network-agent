"""Tool for analyzing historical syslog data using SQLite FTS."""

import sqlite3
from langchain_core.tools import tool
from src.core.models import LogAnalysisOutput
from src.core.config import settings

# Setup for the log analysis tool
DB_PATH = settings.log_database_file


@tool
def analyze_logs(query: str) -> LogAnalysisOutput:
    """
    Analyzes historical syslogs to answer questions about past network events.
    Use this when the user asks about errors, flaps, changes, or events that happened in the past.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This allows us to access columns by name

        # Use FTS (Full Text Search) to find relevant logs
        cursor = conn.cursor()

        relevant_logs = []

        # Try FTS with different query formats - only use valid FTS syntax
        try:
            # Simple term search
            cursor.execute(
                """
                SELECT log_entry FROM syslog_fts
                WHERE syslog_fts MATCH ?
                ORDER BY rank
                LIMIT 5
            """,
                (query,),
            )

            rows = cursor.fetchall()
            relevant_logs = [row["log_entry"] for row in rows]
        except sqlite3.Error:
            # If FTS fails, continue with LIKE search
            pass

        # If FTS didn't return results, do a simple LIKE search with OR conditions
        if not relevant_logs:
            # Split query into words and search for any of them
            query_words = query.lower().split()
            where_conditions = " OR ".join(
                ["log_message LIKE ? OR device_name LIKE ?"] * len(query_words)
            )
            params = []
            for word in query_words:
                params.extend([f"%{word}%", f"%{word}%"])

            cursor.execute(
                f"""
                SELECT log_entry FROM syslog
                WHERE {where_conditions}
                ORDER BY id
                LIMIT 5
            """,
                params,
            )

            rows = cursor.fetchall()
            relevant_logs = [row["log_entry"] for row in rows]

        # If still no results, try a simple contains search
        if not relevant_logs:
            cursor.execute(
                """
                SELECT log_entry FROM syslog
                WHERE log_entry LIKE ?
                ORDER BY id
                LIMIT 5
            """,
                (f"%{query}%",),
            )

            rows = cursor.fetchall()
            relevant_logs = [row["log_entry"] for row in rows]

        conn.close()

        if not relevant_logs:
            summary = "No relevant logs found for that query."
        else:
            summary = f"Found {len(relevant_logs)} relevant log entry(s). Please review the provided logs."

        return LogAnalysisOutput(
            query=query, relevant_logs=relevant_logs, summary=summary
        )
    except Exception as e:
        # This can happen if the DB doesn't exist yet
        return LogAnalysisOutput(
            query=query,
            relevant_logs=[],
            summary=f"Error analyzing logs: {e}. Please ensure the log database has been created by running 'scripts/ingest_logs.py'.",
        )
