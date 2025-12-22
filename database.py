import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("inventory.db", check_same_thread=False)
    cursor = conn.cursor()
    # Create the tools table
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
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tools")
    data = cursor.fetchall()
    conn.close()
    return data

def update_tool_status(qr_id, worker, status, return_date=None):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tools 
        SET status=?, last_worker=?, expected_return=? 
        WHERE qr_id=?""", (status, worker, return_date, qr_id))
    conn.commit()
    conn.close()