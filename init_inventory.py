import sqlite3

def setup():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # 1. CREATE THE TABLE FIRST (This prevents the "no such table" error)
    cursor.execute('''CREATE TABLE IF NOT EXISTS tools (
        id INTEGER PRIMARY KEY,
        qr_id TEXT UNIQUE,
        name TEXT,
        status TEXT DEFAULT 'Available',
        last_worker TEXT,
        expected_return TEXT
    )''')

    # 2. Add the test tools
    test_tools = [
        ('DRL-101', 'DeWalt Cordless Drill'),
        ('SAW-202', 'Circular Saw'),
        ('GEN-303', 'Portable Generator')
    ]

    try:
        cursor.executemany("INSERT OR IGNORE INTO tools (qr_id, name, status) VALUES (?, ?, 'Available')", test_tools)
        conn.commit()
        print("✅ Success: Table created and test tools added!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup()