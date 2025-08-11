import json
import os
import sqlite3
from typing import Any, Dict, Optional

DB_PATH = os.getenv("DB_PATH", "contacts.db")


def initialize_audit(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def record_event(event_type: str, details: Dict[str, Any]) -> None:
    try:
        connection = sqlite3.connect(DB_PATH)
        initialize_audit(connection)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO audit_events (event_type, details) VALUES (?, ?)",
            (event_type, json.dumps(details)),
        )
        connection.commit()
    except Exception:
        # Swallow audit errors to not impact main flow
        pass
    finally:
        try:
            connection.close()
        except Exception:
            pass