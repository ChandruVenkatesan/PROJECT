# Smart Document Indexing System — MySQL Edition

**Register Number:** 7376231MZ104 | **Name:** ABCD

---

## Folder Structure

```
SDIS_MYSQL/
│
├── app.py                   ← Flask entry point
├── .env                     ← MySQL credentials (edit this first!)
├── requirements.txt
├── setup_mysql.sql          ← Run once to create DB + user
├── create_admin.py          ← Run to create/reset admin account
│
├── database/
│   └── db.py                ← MySQL connection pool + table init
│
├── modules/
│   ├── auth.py              ← Login · Register · Logout · Profile
│   ├── extractor.py         ← PDF · DOCX · TXT · OCR extraction
│   ├── indexer.py           ← Keyword index (document_index table)
│   ├── documents.py         ← Upload · Dashboard · View · Download · Delete
│   ├── search.py            ← MySQL FULLTEXT search + LIKE fallback
│   ├── admin.py             ← User mgmt · All docs · Audit logs
│   └── metadata.py          ← Title · Author · Tags · Description
│
├── templates/               ← 13 Jinja2 HTML templates
├── static/css/main.css      ← Dark theme stylesheet
├── static/js/               ← main.js + upload.js
└── uploads/                 ← Uploaded files (auto-created)
```

---

## Setup in 5 Steps

### Step 1 — Install MySQL

**Windows:**
1. Download MySQL Installer → https://dev.mysql.com/downloads/installer/
2. Run installer → choose "Developer Default"
3. Set a root password when prompted — remember it!
4. MySQL Workbench is installed alongside (optional GUI)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
mysql_secure_installation
```

---

### Step 2 — Create the Database

Open terminal and run:
```bash
mysql -u root -p < setup_mysql.sql
```
Enter your root password when asked.

This creates:
- Database: `sdis_db`
- User: `sdis_user` / password: `sdis_password`
- All 5 tables with correct schema

---

### Step 3 — Configure .env

Edit the `.env` file with your actual MySQL settings:
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=sdis_user
MYSQL_PASSWORD=sdis_password
MYSQL_DATABASE=sdis_db
SECRET_KEY=change-this-to-any-random-string
```

---

### Step 4 — Install Python packages

```bash
pip install -r requirements.txt
```

Also install Tesseract OCR for scanned image support:
- **Windows:** https://github.com/UB-Mannheim/tesseract/wiki
- **Ubuntu:** `sudo apt install tesseract-ocr`
- **macOS:** `brew install tesseract`

---

### Step 5 — Run

```bash
python app.py
```

Open → **http://localhost:5000**
Login → **admin / Admin@123**

Or create your own admin:
```bash
python create_admin.py
```

---

## MySQL vs SQLite Differences

| Feature | SQLite (old) | MySQL (this) |
|---|---|---|
| Search | FTS5 virtual table | FULLTEXT INDEX (InnoDB) |
| Connection | File-based | TCP connection pool |
| Concurrency | Limited | Full multi-user |
| Scale | Small projects | Production-ready |
| Config | None | .env credentials |
| Tables | Same schema | Same schema |
