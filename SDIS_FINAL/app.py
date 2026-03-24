"""
╔══════════════════════════════════════════════════════╗
║   SMART DOCUMENT INDEXING SYSTEM (SDIS)              ║
║   app.py — Main Entry Point                          ║
║   Run: python app.py  →  http://localhost:5000       ║
╚══════════════════════════════════════════════════════╝
"""

import os
from flask import Flask, render_template, redirect, session

# ── Create Flask app ─────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sdis-secret-key-2024")

# ── Config ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["UPLOAD_FOLDER"]        = os.path.join(BASE_DIR, "uploads")
app.config["MAX_CONTENT_LENGTH"]   = 50 * 1024 * 1024          # 50 MB
app.config["ALLOWED_EXTENSIONS"]   = {"pdf", "png", "jpg", "jpeg", "docx", "txt"}

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

# ── Root Route ────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/documents/dashboard")
    return render_template("index.html")

# ── Bootstrap & Run ───────────────────────────────────────
if __name__ == "__main__":
    from database.db import init_db
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db()
    print("\n  ◈  SDIS Running  →  http://localhost:5000")
    print("     Admin login   →  admin / Admin@123\n")
    app.run(debug=True, port=5000)
