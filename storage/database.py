import sqlite3
from datetime import datetime

DB_PATH = "codereview.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS developer_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        repo TEXT,
        pr_number INTEGER,
        category TEXT,
        comment TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS developer_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        category TEXT,
        occurrence_count INTEGER DEFAULT 1,
        resolved INTEGER DEFAULT 0,
        last_seen TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS architecture_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT,
        snapshot TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS open_prs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT,
        pr_number INTEGER,
        author TEXT,
        changed_files TEXT,
        opened_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS installations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        installation_id INTEGER,
        repo TEXT,
        installed_at TEXT
    )""")

    conn.commit()
    conn.close()
    print("[DB] Database initialized")


def save_comment(username: str, repo: str, pr_number: int, category: str, comment: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO developer_comments VALUES (NULL,?,?,?,?,?,?)",
        (username, repo, pr_number, category, comment, datetime.now().isoformat()),
    )
    c.execute(
        "SELECT id, occurrence_count FROM developer_patterns WHERE username=? AND category=?",
        (username, category),
    )
    row = c.fetchone()
    if row:
        c.execute(
            "UPDATE developer_patterns SET occurrence_count=occurrence_count+1, last_seen=? WHERE id=?",
            (datetime.now().isoformat(), row[0]),
        )
    else:
        c.execute(
            "INSERT INTO developer_patterns VALUES (NULL,?,?,1,0,?)",
            (username, category, datetime.now().isoformat()),
        )
    conn.commit()
    conn.close()


def get_patterns(username: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """SELECT category, occurrence_count FROM developer_patterns
           WHERE username=? AND resolved=0
           ORDER BY occurrence_count DESC""",
        (username,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def resolve_pattern(username: str, category: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE developer_patterns SET resolved=1 WHERE username=? AND category=?",
        (username, category),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    save_comment("aarush", "test-repo", 1, "security", "Missing input validation")
    save_comment("aarush", "test-repo", 2, "security", "SQL injection risk")
    print(get_patterns("aarush"))
