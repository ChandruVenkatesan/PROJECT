"""
╔══════════════════════════════════════════════════════╗
║   SMART DOCUMENT INDEXING SYSTEM (SDIS)              ║
║   app.py  —  Main Entry Point (MySQL edition)        ║
║   Local : python app.py → http://localhost:5000      ║
║   Deploy: gunicorn app:app                           ║
╚══════════════════════════════════════════════════════╝
"""

import os
from flask import Flask, render_template, redirect, session

# ── Load .env ────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Flask app ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sdis-secret-key-change-me")

# ── Upload folder ─────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024        # 50 MB
app.config["ALLOWED_EXTENSIONS"] = {"pdf","png","jpg","jpeg","docx","txt"}

# ── Register Blueprints ───────────────────────────────────
from modules.auth      import auth_bp
from modules.documents import docs_bp
from modules.search    import search_bp
from modules.admin     import admin_bp
from modules.metadata  import meta_bp

app.register_blueprint(auth_bp,   url_prefix="/auth")
app.register_blueprint(docs_bp,   url_prefix="/documents")
app.register_blueprint(search_bp, url_prefix="/search")
app.register_blueprint(admin_bp,  url_prefix="/admin")
app.register_blueprint(meta_bp,   url_prefix="/metadata")

# ── Root ──────────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/documents/dashboard")
    return render_template("index.html")

# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    from database.db import init_db
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    print("\n  ◈  SDIS (MySQL) →  http://localhost:5000")
    print("     Admin login  →  Chandru / Chandru@2005\n")
    app.run(debug=True, port=5000)
