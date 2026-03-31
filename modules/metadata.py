"""
modules/metadata.py
───────────────────
Update and fetch document metadata: title · author · tags · description
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
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT user_id FROM documents WHERE id=%s AND is_deleted=0", (doc_id,)
    )
    doc = cur.fetchone()

    if not doc or (doc["user_id"] != session["user_id"]
                   and session.get("role") != "admin"):
        cur.close()
        conn.close()
        flash("Access denied.", "error")
        return redirect(url_for("docs.dashboard"))

    cur.execute("SELECT id FROM metadata WHERE doc_id=%s", (doc_id,))
    exists = cur.fetchone()

    if exists:
        cur.execute("""
            UPDATE metadata SET title=%s, author=%s, tags=%s, description=%s
            WHERE doc_id=%s
        """, (title, author, tags, desc, doc_id))
    else:
        cur.execute("""
            INSERT INTO metadata (doc_id, title, author, tags, description)
            VALUES (%s,%s,%s,%s,%s)
        """, (doc_id, title, author, tags, desc))

    conn.commit()
    cur.close()
    conn.close()
    flash("Metadata saved.", "success")
    return redirect(url_for("docs.view_document", doc_id=doc_id))


@meta_bp.route("/api/<int:doc_id>")
@login_required
def get_metadata(doc_id):
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM metadata WHERE doc_id=%s", (doc_id,))
    m = cur.fetchone()
    cur.close()
    conn.close()
    if not m:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"doc_id": doc_id, "title": m["title"],
                    "author": m["author"], "tags": m["tags"],
                    "description": m["description"]})
