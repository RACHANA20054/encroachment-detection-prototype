import sqlite3
from datetime import datetime

DB_PATH = "events.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            object_type TEXT,
            confidence REAL,
            fusion_score REAL,
            affected_percent REAL,
            esi REAL,
            severity_level TEXT,
            zone TEXT,
            image_path TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_event(object_type, confidence, fusion_score, affected_percent, esi,
               severity_level, zone="Zone-A", image_path=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO events (timestamp, object_type, confidence, fusion_score,
                             affected_percent, esi, severity_level, zone, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(timespec="seconds"),
        object_type, confidence, fusion_score, affected_percent, esi,
        severity_level, zone, image_path
    ))
    conn.commit()
    conn.close()


def get_recent_events(limit=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
