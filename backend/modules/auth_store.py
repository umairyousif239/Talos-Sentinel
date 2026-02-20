from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "auth.db"

def get_connection():
    # Ensuring the data folder exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False is required for FastAPI to interact with SQLite seamlessly
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            hashed_password TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user_from_db(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, hashed_password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def create_user_in_db(username: str, hashed_password: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (username, hashed_password)
        values (?, ?)
        """, (username, hashed_password))
    conn.commit()
    conn.close()