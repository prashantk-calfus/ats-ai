import sqlite3
from pathlib import Path

DB_PATH = Path("core/data/candidates.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_sqlite_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                uuid TEXT PRIMARY KEY,
                name TEXT,
                ats_score REAL,
                llm_comment TEXT,
                jd_name TEXT
                
            )
        ''')

def insert_candidate(uuid: str, name: str, ats_score: float, llm_comment: str, jd_name: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT OR REPLACE INTO candidates VALUES (?, ?, ?, ?, ?)''',
            (uuid, name, ats_score, llm_comment, jd_name))

def fetch_all_candidates():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT * FROM candidates").fetchall()



init_sqlite_db()
