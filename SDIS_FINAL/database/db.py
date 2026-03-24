"""
database/db.py
──────────────
SQLite connection, table creation, and seeding.
To swap to MySQL: replace sqlite3 with mysql-connector-python
and update get_db_connection() with your credentials.
"""

import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sdis.db")


def get_db_connection():
    """Return a sqlite3 connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # better concurrency
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables + FTS index + seed admin user."""
    conn = get_db_connection()
    cur  = conn.cursor()

    # ── users ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user',
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active   INTEGER  DEFAULT 1
        )""")

    # ── documents ─────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            filename       TEXT    NOT NULL,
            original_name  TEXT    NOT NULL,
            file_type      TEXT    NOT NULL,
            file_size      INTEGER NOT NULL,
            upload_date    DATETIME DEFAULT CURRENT_TIMESTAMP,
            extracted_text TEXT,
            is_deleted     INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""")

    # ── inverted keyword index ────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS document_index (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id    INTEGER NOT NULL,
            keyword   TEXT    NOT NULL,
            frequency INTEGER DEFAULT 1,
            FOREIGN KEY (doc_id) REFERENCES documents(id)
        )""")

    # ── metadata ──────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id      INTEGER NOT NULL UNIQUE,
            title       TEXT,
            author      TEXT,
            tags        TEXT,
            description TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents(id)
        )""")

    # ── audit log ─────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            action    TEXT    NOT NULL,
            detail    TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

    # ── FTS5 virtual table (full-text search with BM25) ───
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_documents
        USING fts5(doc_id UNINDEXED, content, tokenize='porter ascii')
    """)

    # ── seed default admin (password: Admin@123) ──────────
    admin_pw = hashlib.sha256("Admin@123".encode()).hexdigest()
    cur.execute("""
        INSERT OR IGNORE INTO users (username, email, password, role)
        VALUES ('admin', 'admin@sdis.com', ?, 'admin')
    """, (admin_pw,))

    conn.commit()
    conn.close()
    print("[DB] Initialized →", DB_PATH)
