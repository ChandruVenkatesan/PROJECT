# Smart Document Indexing System (SDIS)

**Register Number:** 7376231MZ104 | **Name:** ABCD

---

## Folder Structure

```
SDIS_FINAL/
│
├── app.py                    ← START HERE — Flask app, blueprint registration
├── requirements.txt          ← pip install -r requirements.txt
│
├── database/
│   ├── __init__.py
│   └── db.py                 ← SQLite setup, 5 tables + FTS5 virtual table
│
├── modules/
│   ├── __init__.py
│   ├── auth.py               ← Login · Register · Logout · Profile · Change PW
│   ├── extractor.py          ← PDF (PyMuPDF) · DOCX · TXT · OCR (Tesseract)
│   ├── indexer.py            ← Inverted index + FTS5 BM25 indexer
│   ├── documents.py          ← Upload · Dashboard · View · Download · Delete
│   ├── search.py             ← FTS5 keyword search · Snippets · Filters
│   ├── admin.py              ← User management · Audit logs · System stats
│   └── metadata.py           ← Title · Author · Tags · Description per doc
│
├── templates/                ← Jinja2 HTML (all extend base.html)
│   ├── base.html             ← Master layout + navbar
│   ├── index.html            ← Landing page
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html        ← User document list
│   ├── upload.html           ← Drag & drop multi-file upload
│   ├── search.html           ← Search + results + snippets
│   ├── view_document.html    ← Detail · Metadata editor · Keywords
│   ├── profile.html
│   ├── admin_dashboard.html
│   ├── admin_users.html
│   ├── admin_documents.html
│   └── admin_logs.html
│
├── static/
│   ├── css/main.css          ← Complete dark theme
│   └── js/
│       ├── main.js           ← Flash auto-dismiss
│       └── upload.js         ← Drag & drop preview
│
└── uploads/                  ← Auto-created on first run
```

---

## Request Flow

```
Browser Request
      │
  app.py                    (registers all blueprints)
      │
  ┌───┴────────────────────────────────────────┐
  │  /auth/*     → modules/auth.py             │
  │  /documents/* → modules/documents.py       │
  │                    ↓ uses                  │
  │             modules/extractor.py (text)    │
  │                    ↓ uses                  │
  │             modules/indexer.py (FTS5)      │
  │  /search/*   → modules/search.py           │
  │  /metadata/* → modules/metadata.py         │
  │  /admin/*    → modules/admin.py            │
  └────────────────────────────────────────────┘
      │
  database/db.py              (all DB access via get_db_connection())
      │
  database/sdis.db            (auto-created SQLite file)
```

---

## Setup & Run

```bash
# 1. Install Python packages
pip install -r requirements.txt

# 2. Install Tesseract OCR (for scanned image support)
#    Ubuntu:  sudo apt install tesseract-ocr
#    macOS:   brew install tesseract
#    Windows: https://github.com/UB-Mannheim/tesseract/wiki

# 3. Run
python app.py

# → Open http://localhost:5000
# → Admin: admin / Admin@123
```

---

## Functional Requirements ↔ Module Mapping

| SRS Requirement         | Module                        |
|-------------------------|-------------------------------|
| User Authentication     | `modules/auth.py`             |
| Document Upload         | `modules/documents.py`        |
| Text Extraction (OCR)   | `modules/extractor.py`        |
| Document Indexing       | `modules/indexer.py`          |
| Document Search         | `modules/search.py`           |
| Document Management     | `modules/documents.py`        |
| Metadata Management     | `modules/metadata.py`         |
| Access Control          | `login_required` / `admin_required` decorators in `modules/auth.py` |
| Admin Management        | `modules/admin.py`            |
| Error Handling          | Flash messages + try/except in each module |
