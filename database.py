import sqlite3
from datetime import datetime

def init_db():
    """Initializes the offline database and creates the tools table."""
    conn = sqlite3.connect("inventory.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tools (
        id INTEGER PRIMARY KEY,
        qr_id TEXT UNIQUE,
        name TEXT,
        status TEXT DEFAULT 'Available',
        last_worker TEXT,
        expected_return TEXT
    )''')
    conn.commit()
    conn.close()

def get_all_tools():
    """Fetches all tools for the dashboard list."""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tools")
    data = cursor.fetchall()
    conn.close()
    return data

def get_tool_by_id(qr_id):
    """Checks if a tool exists and returns its data row."""
    conn = sqlite3.connect("inventory.db")
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tools WHERE qr_id=?", (qr_id,))
    tool = cursor.fetchone()
    conn.close()
    return tool

def update_tool_status(qr_id, worker, status, return_date=None):
    """Updates the database when a tool is checked in or out."""
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tools 
        SET status=?, last_worker=?, expected_return=? 
        WHERE qr_id=?""", (status, worker, return_date, qr_id))
    conn.commit()
    conn.close()