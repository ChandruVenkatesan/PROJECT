"""
modules/admin.py
────────────────
Admin-only views: Dashboard · Users · All Docs · Audit Logs
Blueprint prefix: /admin
"""

import hashlib
from flask import (Blueprint, render_template, request,
                   redirect, session, flash, url_for)
from database.db  import get_db_connection
from modules.auth import admin_required
from modules.indexer import total_indexed

admin_bp = Blueprint("admin", __name__)


def _fmt(b):
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


# ── Admin Dashboard ───────────────────────────────────────

@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_docs  = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE is_deleted=0").fetchone()[0]
    total_size  = conn.execute(
        "SELECT SUM(file_size) FROM documents WHERE is_deleted=0"
    ).fetchone()[0] or 0
    recent_logs = conn.execute("""
        SELECT a.*, u.username FROM audit_log a
        LEFT JOIN users u ON u.id=a.user_id
        ORDER BY a.timestamp DESC LIMIT 20
    """).fetchall()
    type_stats = conn.execute("""
        SELECT file_type, COUNT(*) cnt FROM documents
        WHERE is_deleted=0 GROUP BY file_type
    """).fetchall()
    conn.close()

    return render_template("admin_dashboard.html",
                           total_users=total_users,
                           total_docs=total_docs,
                           total_size=_fmt(total_size),
                           recent_logs=recent_logs,
                           file_type_stats=type_stats,
                           indexed_docs=total_indexed())


# ── User Management ───────────────────────────────────────

@admin_bp.route("/users")
@admin_required
def manage_users():
    conn  = get_db_connection()
    users = conn.execute("""
        SELECT u.*, COUNT(d.id) doc_count FROM users u
        LEFT JOIN documents d ON d.user_id=u.id AND d.is_deleted=0
        GROUP BY u.id ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/users/toggle/<int:uid>", methods=["POST"])
@admin_required
def toggle_user(uid):
    if uid == session["user_id"]:
        flash("Cannot modify your own account.", "error")
        return redirect(url_for("admin.manage_users"))
    conn = get_db_connection()
    cur  = conn.execute("SELECT is_active FROM users WHERE id=?", (uid,)).fetchone()
    new  = 0 if cur["is_active"] else 1
    conn.execute("UPDATE users SET is_active=? WHERE id=?", (new, uid))
    conn.commit()
    conn.close()
    flash(f"User {'activated' if new else 'deactivated'}.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/delete/<int:uid>", methods=["POST"])
@admin_required
def delete_user(uid):
    if uid == session["user_id"]:
        flash("Cannot delete your own account.", "error")
        return redirect(url_for("admin.manage_users"))
    conn = get_db_connection()
    conn.execute("UPDATE documents SET is_deleted=1 WHERE user_id=?", (uid,))
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    flash("User deleted.", "success")
    return redirect(url_for("admin.manage_users"))


# ── All Documents ─────────────────────────────────────────

@admin_bp.route("/documents")
@admin_required
def all_documents():
    conn = get_db_connection()
    docs = conn.execute("""
        SELECT d.*, u.username FROM documents d
        JOIN users u ON u.id=d.user_id
        WHERE d.is_deleted=0 ORDER BY d.upload_date DESC
    """).fetchall()
    conn.close()
    return render_template("admin_documents.html", documents=docs)


# ── Audit Logs ────────────────────────────────────────────

@admin_bp.route("/logs")
@admin_required
def audit_logs():
    conn = get_db_connection()
    logs = conn.execute("""
        SELECT a.*, u.username FROM audit_log a
        LEFT JOIN users u ON u.id=a.user_id
        ORDER BY a.timestamp DESC LIMIT 200
    """).fetchall()
    conn.close()
    return render_template("admin_logs.html", logs=logs)
