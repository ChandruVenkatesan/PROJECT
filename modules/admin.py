"""
modules/admin.py
────────────────
Admin dashboard · User management · All Documents · Audit Logs
Blueprint prefix: /admin
"""

import hashlib
from flask import (Blueprint, render_template, request,
                   redirect, session, flash, url_for)
from database.db  import get_db_connection, log_action
from modules.auth import admin_required
from modules.indexer import total_indexed

admin_bp = Blueprint("admin", __name__)


def _fmt(b):
    b = b or 0
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def _fix_dates(rows):
    """Convert datetime objects to strings for Jinja2 templates."""
    if rows is None:
        return None
    if isinstance(rows, dict):
        return {k: (str(v) if hasattr(v, 'strftime') else v) for k, v in rows.items()}
    return [{k: (str(v) if hasattr(v, 'strftime') else v)
             for k, v in row.items()} for row in rows]


# ── Admin Dashboard ───────────────────────────────────────

@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) cnt FROM users")
    total_users = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) cnt FROM documents WHERE is_deleted=0")
    total_docs = cur.fetchone()["cnt"]

    cur.execute("SELECT COALESCE(SUM(file_size),0) total FROM documents WHERE is_deleted=0")
    total_size = cur.fetchone()["total"]

    cur.execute("""
        SELECT a.*, u.username FROM audit_log a
        LEFT JOIN users u ON u.id=a.user_id
        ORDER BY a.timestamp DESC LIMIT 20
    """)
    recent_logs = _fix_dates(cur.fetchall())

    cur.execute("""
        SELECT file_type, COUNT(*) cnt FROM documents
        WHERE is_deleted=0 GROUP BY file_type
    """)
    type_stats = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin_dashboard.html",
                           total_users=total_users,
                           total_docs=total_docs,
                           total_size=_fmt(total_size),
                           recent_logs=recent_logs,
                           file_type_stats=type_stats,
                           indexed_docs=total_indexed())


# ── Manage Users ──────────────────────────────────────────

@admin_bp.route("/users")
@admin_required
def manage_users():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.*, COUNT(d.id) doc_count FROM users u
        LEFT JOIN documents d ON d.user_id=u.id AND d.is_deleted=0
        GROUP BY u.id ORDER BY u.created_at DESC
    """)
    users = _fix_dates(cur.fetchall())
    cur.close()
    conn.close()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/users/toggle/<int:uid>", methods=["POST"])
@admin_required
def toggle_user(uid):
    if uid == session["user_id"]:
        flash("Cannot modify your own account.", "error")
        return redirect(url_for("admin.manage_users"))
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT is_active FROM users WHERE id=%s", (uid,))
    row = cur.fetchone()
    new = 0 if row["is_active"] else 1
    cur.execute("UPDATE users SET is_active=%s WHERE id=%s", (new, uid))
    conn.commit()
    cur.close()
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
    cur  = conn.cursor()
    cur.execute("UPDATE documents SET is_deleted=1 WHERE user_id=%s", (uid,))
    cur.execute("DELETE FROM users WHERE id=%s", (uid,))
    conn.commit()
    cur.close()
    conn.close()
    flash("User deleted.", "success")
    return redirect(url_for("admin.manage_users"))


# ── All Documents ─────────────────────────────────────────

@admin_bp.route("/documents")
@admin_required
def all_documents():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT d.*, u.username FROM documents d
        JOIN users u ON u.id=d.user_id
        WHERE d.is_deleted=0 ORDER BY d.upload_date DESC
    """)
    docs = _fix_dates(cur.fetchall())
    cur.close()
    conn.close()
    return render_template("admin_documents.html", documents=docs)


# ── Audit Logs ────────────────────────────────────────────

@admin_bp.route("/logs")
@admin_required
def audit_logs():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, u.username FROM audit_log a
        LEFT JOIN users u ON u.id=a.user_id
        ORDER BY a.timestamp DESC LIMIT 200
    """)
    logs = _fix_dates(cur.fetchall())
    cur.close()
    conn.close()
    return render_template("admin_logs.html", logs=logs)