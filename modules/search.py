"""
modules/search.py
─────────────────
MySQL FULLTEXT search (MATCH ... AGAINST) with LIKE fallback.
Blueprint prefix: /search
"""

import re
from flask import Blueprint, render_template, request, session, redirect, url_for
from database.db  import get_db_connection
from modules.auth import login_required

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
@login_required
def search():
    q       = request.args.get("q",    "").strip()
    f_type  = request.args.get("type", "all")
    sort_by = request.args.get("sort", "relevance")
    results = []
    total   = 0

    if q:
        results, total = _search(q, session["user_id"],
                                 session.get("role", "user"),
                                 f_type, sort_by)

    return render_template("search.html",
                           query=q, results=results, total=total,
                           filter_type=f_type, sort_by=sort_by)


def _search(query, user_id, role, f_type, sort_by):
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)

    type_cond  = "AND d.file_type=%s" if f_type != "all" else ""
    type_param = [f_type]             if f_type != "all" else []

    # ── Try MySQL FULLTEXT search first ───────────────────
    try:
        if role == "admin":
            cur.execute(f"""
                SELECT d.*, m.tags,
                       MATCH(d.extracted_text) AGAINST (%s IN NATURAL LANGUAGE MODE) AS score
                FROM documents d
                LEFT JOIN metadata m ON m.doc_id = d.id
                WHERE d.is_deleted=0
                  AND MATCH(d.extracted_text) AGAINST (%s IN NATURAL LANGUAGE MODE)
                  {type_cond}
                ORDER BY score DESC
            """, [query, query] + type_param)
        else:
            cur.execute(f"""
                SELECT d.*, m.tags,
                       MATCH(d.extracted_text) AGAINST (%s IN NATURAL LANGUAGE MODE) AS score
                FROM documents d
                LEFT JOIN metadata m ON m.doc_id = d.id
                WHERE d.user_id=%s AND d.is_deleted=0
                  AND MATCH(d.extracted_text) AGAINST (%s IN NATURAL LANGUAGE MODE)
                  {type_cond}
                ORDER BY score DESC
            """, [query, user_id, query] + type_param)

        docs = cur.fetchall()

        # If FULLTEXT returns nothing try LIKE fallback
        if not docs:
            raise ValueError("no fulltext results")

    except Exception:
        # ── LIKE fallback ─────────────────────────────────
        like = f"%{query}%"
        if role == "admin":
            cur.execute(f"""
                SELECT d.*, m.tags, 0 AS score
                FROM documents d
                LEFT JOIN metadata m ON m.doc_id = d.id
                WHERE d.is_deleted=0
                  AND d.extracted_text LIKE %s
                  {type_cond}
                ORDER BY d.upload_date DESC
            """, [like] + type_param)
        else:
            cur.execute(f"""
                SELECT d.*, m.tags, 0 AS score
                FROM documents d
                LEFT JOIN metadata m ON m.doc_id = d.id
                WHERE d.user_id=%s AND d.is_deleted=0
                  AND d.extracted_text LIKE %s
                  {type_cond}
                ORDER BY d.upload_date DESC
            """, [user_id, like] + type_param)
        docs = cur.fetchall()

    cur.close()
    conn.close()

    results = []
    for doc in docs:
        results.append({
            "id":            doc["id"],
            "original_name": doc["original_name"],
            "file_type":     doc["file_type"],
            "upload_date":   str(doc["upload_date"])[:10],
            "file_size":     doc["file_size"],
            "tags":          doc["tags"],
            "snippet":       _snippet(doc["extracted_text"] or "", query),
            "score":         float(doc.get("score") or 0),
        })

    # Re-sort if needed
    if sort_by == "date":
        results.sort(key=lambda x: x["upload_date"], reverse=True)
    elif sort_by == "name":
        results.sort(key=lambda x: x["original_name"].lower())

    return results, len(results)


def _snippet(text, query, window=150):
    if not text:
        return ""
    lo    = text.lower()
    word  = query.lower().split()[0]
    idx   = lo.find(word)
    start = max(0, (idx - 60) if idx != -1 else 0)
    end   = min(len(text), start + window)
    snip  = text[start:end]
    snip  = re.sub(f"(?i)({re.escape(query.split()[0])})",
                   r"<mark>\1</mark>", snip)
    return ("…" if start else "") + snip + "…"
