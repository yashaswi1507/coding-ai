import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), "thinkcode.db")

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'guest',
        problem_id TEXT NOT NULL,
        thinking_score INTEGER DEFAULT 0,
        code_score INTEGER DEFAULT 0,
        passed INTEGER DEFAULT 0,
        total INTEGER DEFAULT 0,
        topic TEXT, difficulty TEXT,
        thinking_text TEXT, user_code TEXT,
        ai_feedback TEXT, code_approach TEXT,
        language TEXT DEFAULT 'python',
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS streaks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'guest',
        date TEXT NOT NULL,
        problems_solved INTEGER DEFAULT 0,
        UNIQUE(user_id, date)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mentor_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE DEFAULT 'guest',
        weak_topics TEXT DEFAULT '[]',
        strong_topics TEXT DEFAULT '[]',
        avg_thinking_score REAL DEFAULT 0,
        total_submissions INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS leaderboard (
        user_id TEXT PRIMARY KEY,
        display_name TEXT DEFAULT 'Anonymous',
        total_thinking_score INTEGER DEFAULT 0,
        submissions_count INTEGER DEFAULT 0,
        avg_thinking_score REAL DEFAULT 0,
        current_streak INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        achievement_id TEXT NOT NULL,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, achievement_id)
    )""")

    conn.commit()
    conn.close()

def add_xp_tables():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS user_xp (
        user_id TEXT PRIMARY KEY,
        total_xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS xp_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        xp_gained INTEGER DEFAULT 0,
        reason TEXT,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()