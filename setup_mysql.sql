-- ══════════════════════════════════════════════
--  SDIS — MySQL Setup Script
--  Run this ONCE as root/admin MySQL user:
--  mysql -u root -p < setup_mysql.sql
-- ══════════════════════════════════════════════

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS sdis_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2. Create a dedicated user (change password if you want)
CREATE USER IF NOT EXISTS 'sdis_user'@'localhost'
    IDENTIFIED BY 'sdis_password';

-- 3. Grant full access on sdis_db only
GRANT ALL PRIVILEGES ON sdis_db.* TO 'sdis_user'@'localhost';

-- 4. Apply
FLUSH PRIVILEGES;

-- 5. Switch to the database
USE sdis_db;

-- ── Tables ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(80)  NOT NULL UNIQUE,
    email       VARCHAR(120) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(20)  NOT NULL DEFAULT 'user',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    is_active   TINYINT(1)   DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FULLTEXT INDEX ft_extracted (extracted_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS document_index (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    doc_id    INT          NOT NULL,
    keyword   VARCHAR(100) NOT NULL,
    frequency INT          DEFAULT 1,
    INDEX idx_keyword (keyword),
    INDEX idx_doc     (doc_id),
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS metadata (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    doc_id      INT          NOT NULL UNIQUE,
    title       VARCHAR(255),
    author      VARCHAR(120),
    tags        VARCHAR(500),
    description TEXT,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS audit_log (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT,
    action    VARCHAR(50) NOT NULL,
    detail    TEXT,
    timestamp DATETIME    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ts (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ── Default admin account (password: Admin@123) ────────
-- SHA-256 hash of "Admin@123"
INSERT IGNORE INTO users (username, email, password, role)
VALUES (
    'admin',
    'admin@sdis.com',
    'c7f4a3e3e2a2e3c3e2a2e3c3e2a2e3c3e2a2e3c3e2a2e3c3e2a2e3c3e2a2e3',
    'admin'
);

-- NOTE: The hash above is a placeholder.
-- Run  python create_admin.py  after setup to set the real password.

SELECT 'SDIS MySQL setup complete!' AS Status;
