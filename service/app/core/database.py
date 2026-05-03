"""SQLite 连接与数据库初始化逻辑。"""

import sqlite3
import os
from uuid import uuid4

from app.core.security import hash_password

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'social_algorithm.db')

def get_db() -> sqlite3.Connection:
    """获取启用外键约束的数据库连接。"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """初始化业务表结构并写入基础数据。"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    user_columns = cursor.fetchall()
    if user_columns:
      id_column = next((col for col in user_columns if col[1] == "id"), None)
      if id_column and str(id_column[2]).upper() != "TEXT":
        cursor.execute("DROP TABLE IF EXISTS article_tags")
        cursor.execute("DROP TABLE IF EXISTS uploads")
        cursor.execute("DROP TABLE IF EXISTS articles")
        cursor.execute("DROP TABLE IF EXISTS tags")
        cursor.execute("DROP TABLE IF EXISTS users")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("PRAGMA table_info(users)")
    user_columns_after_create = [col[1] for col in cursor.fetchall()]
    if "avatar_url" not in user_columns_after_create:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    if "is_admin" not in user_columns_after_create:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS article_tags (
        article_id TEXT,
        tag_id TEXT,
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY (article_id, tag_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploads (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        uploaded_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS article_likes (
        article_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (article_id, user_id),
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS article_comments (
        id TEXT PRIMARY KEY,
        article_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_follows (
        follower_id TEXT NOT NULL,
        followee_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (follower_id, followee_id),
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (followee_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_behaviors (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        article_id TEXT NOT NULL,
        category TEXT NOT NULL,
        behavior_type TEXT NOT NULL,
        weight REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS algorithm_settings (
        key TEXT PRIMARY KEY,
        value REAL NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS article_dwell_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        article_id TEXT NOT NULL,
        dwell_seconds REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
    )
    """)

    default_settings = {
        "decay_factor": 0.95,
        "similarity_weight": 0.6,
        "hot_weight": 0.2,
        "follow_weight": 0.15,
        "liked_weight": 0.05,
        "diversity_penalty": 0.2,
        "hot_like_factor": 0.15,
        "hot_comment_factor": 0.25,
        "algo_mode": 0,
        "dwell_threshold_seconds": 15,
    }
    for key, value in default_settings.items():
        cursor.execute(
            "INSERT OR IGNORE INTO algorithm_settings (key, value) VALUES (?, ?)",
            (key, value)
        )

    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute(
            "INSERT INTO users (id, username, password_hash, is_admin) VALUES (?, ?, ?, 1)",
            (str(uuid4()), "admin", hash_password("admin"))
        )
    else:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ("admin",))

    conn.commit()
    conn.close()

init_db()
