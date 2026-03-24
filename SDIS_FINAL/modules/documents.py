"""
modules/documents.py
────────────────────
Handles: Upload · Dashboard · View · Download · Delete
Blueprint prefix: /documents
Data flow: Upload → extractor → indexer → DB
"""

import os
import uuid
from flask import (Blueprint, render_template, request, redirect,
                   session, flash, url_for, send_from_directory, current_app)
from database.db  import get_db_connection
from modules.auth import login_required
from modules.extractor import extract_text
from modules.indexer   import index_document, remove_index, top_keywords, index_stats

docs_bp = Blueprint("docs", __name__)

ALLOWED = {"pdf", "png", "jpg", "jpeg", "docx", "txt"}


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

def _fmt(b):
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


# ── Dashboard ─────────────────────────────────────────────

@docs_bp.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    docs = conn.execute("""
        SELECT d.*, m.tags FROM documents d
        LEFT JOIN metadata m ON m.doc_id = d.id
        WHERE d.user_id=? AND d.is_deleted=0
        ORDER BY d.upload_date DESC
    """, (session["user_id"],)).fetchall()
    total_size = sum(d["file_size"] for d in docs)
    conn.close()
    return render_template("dashboard.html",
                           documents=docs,
                           total_docs=len(docs),
                           total_size=_fmt(total_size))


# ── Upload ────────────────────────────────────────────────

@docs_bp.route("/upload", methods=["GET","POST"])
@login_required
def upload():
    if request.method == "POST":
        files = request.files.getlist("documents")
        if not files or all(f.filename == "" for f in files):
            flash("No files selected.", "error")
            return render_template("upload.html")

        ok = 0
        for f in files:
            if not f or not _allowed(f.filename):
                flash(f"'{f.filename}' format not supported.", "warning")
                continue
            ext      = f.filename.rsplit(".", 1)[1].lower()
            safe     = f"{uuid.uuid4().hex}.{ext}"
            path     = os.path.join(current_app.config["UPLOAD_FOLDER"], safe)
            f.save(path)
            size     = os.path.getsize(path)
            text     = extract_text(path, ext)

            conn = get_db_connection()
            cur  = conn.execute("""
                INSERT INTO documents
                    (user_id, filename, original_name, file_type, file_size, extracted_text)
                VALUES (?,?,?,?,?,?)
            """, (session["user_id"], safe, f.filename, ext, size, text))
            doc_id = cur.lastrowid
            conn.execute("INSERT INTO metadata (doc_id, title) VALUES (?,?)",
                         (doc_id, f.filename))
            conn.commit()
            conn.close()

            index_document(doc_id, text)
            ok += 1

        if ok:
            flash(f"{ok} file(s) uploaded and indexed successfully.", "success")
        return redirect(url_for("docs.dashboard"))

    return render_template("upload.html")


# ── View ──────────────────────────────────────────────────

@docs_bp.route("/view/<int:doc_id>")
@login_required
def view_document(doc_id):
    conn = get_db_connection()
    doc  = conn.execute(
        "SELECT * FROM documents WHERE id=? AND is_deleted=0", (doc_id,)
    ).fetchone()

    if not doc or (doc["user_id"] != session["user_id"]
                   and session.get("role") != "admin"):
        flash("Document not found or access denied.", "error")
        conn.close()
        return redirect(url_for("docs.dashboard"))

    meta = conn.execute(
        "SELECT * FROM metadata WHERE doc_id=?", (doc_id,)
    ).fetchone()
    conn.close()

    return render_template("view_document.html",
                           doc=doc, meta=meta,
                           keywords=top_keywords(doc_id),
                           stats=index_stats(doc_id))


# ── Download ──────────────────────────────────────────────

@docs_bp.route("/download/<int:doc_id>")
@login_required
def download(doc_id):
    conn = get_db_connection()
    doc  = conn.execute(
        "SELECT * FROM documents WHERE id=? AND is_deleted=0", (doc_id,)
    ).fetchone()
    conn.close()
    if not doc or (doc["user_id"] != session["user_id"]
                   and session.get("role") != "admin"):
        flash("Access denied.", "error")
        return redirect(url_for("docs.dashboard"))
    return send_from_directory(current_app.config["UPLOAD_FOLDER"],
                               doc["filename"],
                               as_attachment=True,
                               download_name=doc["original_name"])


# ── Delete ────────────────────────────────────────────────

@docs_bp.route("/delete/<int:doc_id>", methods=["POST"])
@login_required
def delete_document(doc_id):
    conn = get_db_connection()
    doc  = conn.execute(
        "SELECT * FROM documents WHERE id=? AND is_deleted=0", (doc_id,)
    ).fetchone()
    if not doc or (doc["user_id"] != session["user_id"]
                   and session.get("role") != "admin"):
        flash("Access denied.", "error")
        conn.close()
        return redirect(url_for("docs.dashboard"))

    conn.execute("UPDATE documents SET is_deleted=1 WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    remove_index(doc_id)
    flash("Document deleted.", "success")
    return redirect(url_for("docs.dashboard"))
