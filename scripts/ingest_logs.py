"""One-time script to process and ingest syslogs into SQLite database."""
import sqlite3
import re

# Configuration
LOG_FILE_PATH = "./syslogs.log"
DB_PATH = "./syslogs.db"

def parse_log_line(line):
    """Parse a syslog line to extract components."""
    if not line.strip():
        return None, None, line.strip()

    # Extract timestamp, device, and message
    match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.*)', line)
    if match:
        timestamp = match.group(1)
        device_name = match.group(2)
        log_message = match.group(3)
        return timestamp, device_name, log_message
    else:
        # If the line doesn't match our expected format, store as is
        return None, None, line.strip()

def main():
    """Loads and ingests logs into SQLite database with FTS."""
    print("Starting log ingestion process...")

    # Connect to SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table for logs (if not exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS syslog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            device_name TEXT,
            log_message TEXT,
            log_entry TEXT  -- Full log entry as it appeared in the file
        )
    """)

    # Create FTS table for full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS syslog_fts USING fts5(
            timestamp,
            device_name,
            log_message,
            log_entry,
            content='syslog'
        )
    """)

    # Clear existing data
    cursor.execute("DELETE FROM syslog")
    print("Cleared existing log data.")

    # Read and process log file
    with open(LOG_FILE_PATH, 'r') as f:
        log_lines = f.readlines()

    print(f"Loaded {len(log_lines)} log entries from {LOG_FILE_PATH}")

    # Insert each log line into the database
    for idx, line in enumerate(log_lines):
        line = line.strip()
        if not line:
            continue

        timestamp, device_name, log_message = parse_log_line(line)

        cursor.execute("""
            INSERT INTO syslog (timestamp, device_name, log_message, log_entry)
            VALUES (?, ?, ?, ?)
        """, (timestamp, device_name, log_message, line))

    print(f"Inserted {len(log_lines)} entries into the database.")

    # Rebuild FTS index
    cursor.execute("INSERT INTO syslog_fts(syslog_fts) VALUES('rebuild')")
    print("Rebuilt FTS index for fast searching.")

    # Commit changes and close
    conn.commit()
    conn.close()
    print("✅ Ingestion complete!")
    print(f"SQLite log database created at: {DB_PATH}")

if __name__ == "__main__":
    main()