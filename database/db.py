"""
database/db.py
──────────────
MySQL connection pool and table initialisation.
All modules import get_db_connection() from here.
"""

import os
import hashlib
import mysql.connector
from mysql.connector import pooling

# ── Load .env if python-dotenv is installed ───────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── DB config from environment variables ─────────────────
DB_CONFIG = {
    "host":     os.environ.get("MYSQL_HOST",     "localhost"),
    "port":     int(os.environ.get("MYSQL_PORT", 3306)),
    "user":     os.environ.get("MYSQL_USER",     "sdis_user"),
    "password": os.environ.get("MYSQL_PASSWORD", "sdis_password"),
    "database": os.environ.get("MYSQL_DATABASE", "sdis_db"),
    "charset":  "utf8mb4",
    "collation":"utf8mb4_unicode_ci",
    "autocommit": False,
    "raise_on_warnings": True,
}

# ── Connection pool (5 connections) ───────────────────────
_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        pool_cfg = dict(DB_CONFIG)
        pool_cfg.pop("raise_on_warnings", None)
        _pool = pooling.MySQLConnectionPool(
            pool_name="sdis_pool",
            pool_size=5,
            **pool_cfg
        )
    return _pool


def get_db_connection():
    """Return a pooled MySQL connection."""
    return _get_pool().get_connection()


# ── Table creation SQL ────────────────────────────────────

TABLES = {}

TABLES["users"] = """
    CREATE TABLE IF NOT EXISTS users (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        username    VARCHAR(80)  NOT NULL UNIQUE,
        email       VARCHAR(120) NOT NULL UNIQUE,
        password    VARCHAR(255) NOT NULL,
        role        VARCHAR(20)  NOT NULL DEFAULT 'user',
        created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
        is_active   TINYINT(1)   DEFAULT 1
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["documents"] = """
    CREATE TABLE IF NOT EXISTS documents (
        id             INT AUTO_INCREMENT PRIMARY KEY,
        user_id        INT           NOT NULL,
        filename       VARCHAR(255)  NOT NULL,
        original_name  VARCHAR(255)  NOT NULL,
        file_type      VARCHAR(20)   NOT NULL,
        file_size      BIGINT        NOT NULL,
        upload_date    DATETIME      DEFAULT CURRENT_TIMESTAMP,
        extracted_text LONGTEXT,
        is_deleted     TINYINT(1)    DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["document_index"] = """
    CREATE TABLE IF NOT EXISTS document_index (
        id        INT AUTO_INCREMENT PRIMARY KEY,
        doc_id    INT         NOT NULL,
        keyword   VARCHAR(100) NOT NULL,
        frequency INT          DEFAULT 1,
        INDEX idx_keyword (keyword),
        INDEX idx_doc    (doc_id),
        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["metadata"] = """
    CREATE TABLE IF NOT EXISTS metadata (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        doc_id      INT          NOT NULL UNIQUE,
        title       VARCHAR(255),
        author      VARCHAR(120),
        tags        VARCHAR(500),
        description TEXT,
        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["audit_log"] = """
    CREATE TABLE IF NOT EXISTS audit_log (
        id        INT AUTO_INCREMENT PRIMARY KEY,
        user_id   INT,
        action    VARCHAR(50)  NOT NULL,
        detail    TEXT,
        timestamp DATETIME     DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_ts (timestamp)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Full-text search index on extracted_text
TABLES["ft_index"] = """
    ALTER TABLE documents
    ADD FULLTEXT INDEX IF NOT EXISTS ft_extracted (extracted_text);
"""


def init_db():
    """Create database schema and seed default admin."""
    conn = get_db_connection()
    cur  = conn.cursor()

    # Create tables in order (respecting FK deps)
    for name, sql in TABLES.items():
        if name == "ft_index":
            try:
                cur.execute(sql)
            except Exception:
                pass   # index may already exist
        else:
            cur.execute(sql)

    # Seed default admin: admin / Admin@123
    admin_pw = hashlib.sha256("Admin@123".encode()).hexdigest()
    cur.execute("""
        INSERT IGNORE INTO users (username, email, password, role)
        VALUES (%s, %s, %s, 'admin')
    """, ("admin", "admin@sdis.com", admin_pw))

    conn.commit()
    cur.close()
    conn.close()
    print("[DB] MySQL schema ready.")


def log_action(user_id, action, detail=""):
    """Insert an audit log row."""
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO audit_log (user_id, action, detail) VALUES (%s, %s, %s)",
        (user_id, action, detail)
    )
    conn.commit()
    cur.close()
    conn.close()
