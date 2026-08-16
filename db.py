import sqlite3
import time
from contextlib import contextmanager
from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                lang TEXT DEFAULT 'en',
                points INTEGER DEFAULT 0,
                referred_by INTEGER,
                joined_at INTEGER,
                last_daily_bonus INTEGER DEFAULT 0,
                last_ad_view INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS channel_tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_username TEXT NOT NULL,
                channel_display TEXT,
                points INTEGER NOT NULL,
                active INTEGER DEFAULT 1
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS completed_tasks (
                user_id INTEGER,
                task_id INTEGER,
                completed_at INTEGER,
                PRIMARY KEY (user_id, task_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                req_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                points INTEGER,
                usdt REAL,
                address TEXT,
                status TEXT DEFAULT 'pending',
                created_at INTEGER
            )
        """)


# ---------- Users ----------

def get_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def create_user(user_id: int, username: str, first_name: str, referred_by: int = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, referred_by, joined_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, referred_by, int(time.time())),
        )


def set_lang(user_id: int, lang: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))


def add_points(user_id: int, amount: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))


def deduct_points(user_id: int, amount: int) -> bool:
    """Returns False if insufficient balance."""
    with get_conn() as conn:
        row = conn.execute("SELECT points FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row or row["points"] < amount:
            return False
        conn.execute("UPDATE users SET points = points - ? WHERE user_id=?", (amount, user_id))
        return True


def set_last_daily_bonus(user_id: int, ts: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET last_daily_bonus=? WHERE user_id=?", (ts, user_id))


def set_last_ad_view(user_id: int, ts: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET last_ad_view=? WHERE user_id=?", (ts, user_id))


def count_referrals(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE referred_by=?", (user_id,)).fetchone()
        return row["c"] if row else 0


# ---------- Channel Tasks ----------

def add_channel_task(channel_username: str, channel_display: str, points: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO channel_tasks (channel_username, channel_display, points) VALUES (?, ?, ?)",
            (channel_username, channel_display, points),
        )
        return cur.lastrowid


def get_active_tasks():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM channel_tasks WHERE active=1").fetchall()
        return [dict(r) for r in rows]


def has_completed_task(user_id: int, task_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM completed_tasks WHERE user_id=? AND task_id=?", (user_id, task_id)
        ).fetchone()
        return row is not None


def mark_task_completed(user_id: int, task_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO completed_tasks (user_id, task_id, completed_at) VALUES (?, ?, ?)",
            (user_id, task_id, int(time.time())),
        )


# ---------- Withdrawals ----------

def create_withdrawal(user_id: int, points: int, usdt: float, address: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO withdrawals (user_id, points, usdt, address, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, points, usdt, address, int(time.time())),
        )
        return cur.lastrowid


def get_withdrawal(req_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM withdrawals WHERE req_id=?", (req_id,)).fetchone()
        return dict(row) if row else None


def set_withdrawal_status(req_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE withdrawals SET status=? WHERE req_id=?", (status, req_id))
