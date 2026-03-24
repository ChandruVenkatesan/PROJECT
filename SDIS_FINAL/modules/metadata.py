"""
modules/metadata.py
───────────────────
Update and fetch document metadata (title, author, tags, description).
Blueprint prefix: /metadata
"""

from flask import Blueprint, request, redirect, session, flash, url_for, jsonify
from database.db  import get_db_connection
from modules.auth import login_required

meta_bp = Blueprint("meta", __name__)


@meta_bp.route("/update/<int:doc_id>", methods=["POST"])
@login_required
def update_metadata(doc_id):
    title  = request.form.get("title",       "").strip()
    author = request.form.get("author",      "").strip()
    tags   = request.form.get("tags",        "").strip()
    desc   = request.form.get("description", "").strip()

    conn = get_db_connection()
    doc  = conn.execute(
        "SELECT user_id FROM documents WHERE id=? AND is_deleted=0", (doc_id,)
    ).fetchone()

    if not doc or (doc["user_id"] != session["user_id"]
                   and session.get("role") != "admin"):
        conn.close()
        flash("Access denied.", "error")
        return redirect(url_for("docs.dashboard"))

    exists = conn.execute(
        "SELECT id FROM metadata WHERE doc_id=?", (doc_id,)
    ).fetchone()

    if exists:
        conn.execute("""
            UPDATE metadata SET title=?, author=?, tags=?, description=?
            WHERE doc_id=?
        """, (title, author, tags, desc, doc_id))
    else:
        conn.execute("""
            INSERT INTO metadata (doc_id, title, author, tags, description)
            VALUES (?,?,?,?,?)
        """, (doc_id, title, author, tags, desc))

    conn.commit()
    conn.close()
    flash("Metadata saved.", "success")
    return redirect(url_for("docs.view_document", doc_id=doc_id))


@meta_bp.route("/api/<int:doc_id>")
@login_required
def get_metadata(doc_id):
    """JSON endpoint for metadata."""
    conn = get_db_connection()
    m    = conn.execute(
        "SELECT * FROM metadata WHERE doc_id=?", (doc_id,)
    ).fetchone()
    conn.close()
    if not m:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"doc_id": doc_id, "title": m["title"],
                    "author": m["author"], "tags": m["tags"],
                    "description": m["description"]})
