import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "metrics.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL,
    model TEXT,
    latency_ms REAL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost_usd REAL,
    success INTEGER,
    error TEXT
)
"""


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    return conn


def log_call(model, latency_ms, input_tokens, output_tokens, estimated_cost_usd, success, error):
    conn = _conn()
    with conn:
        conn.execute(
            "INSERT INTO calls (ts, model, latency_ms, input_tokens, output_tokens, "
            "estimated_cost_usd, success, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (time.time(), model, latency_ms, input_tokens, output_tokens,
             estimated_cost_usd, int(success), error),
        )
    conn.close()


def get_total_cost():
    conn = _conn()
    row = conn.execute("SELECT COALESCE(SUM(estimated_cost_usd), 0) FROM calls").fetchone()
    conn.close()
    return row[0] or 0.0


def get_recent_calls(limit=50):
    conn = _conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT ts, model, latency_ms, input_tokens, output_tokens, "
        "estimated_cost_usd, success, error FROM calls ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
