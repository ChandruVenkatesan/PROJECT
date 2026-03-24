"""
modules/search.py
─────────────────
FTS5 full-text search with BM25 ranking.
Falls back to LIKE search if FTS fails.
Blueprint prefix: /search
"""

import re
from flask import Blueprint, render_template, request, session, redirect, url_for
from database.db     import get_db_connection
from modules.auth    import login_required
from modules.extractor import clean_text

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
@login_required
def search():
    q        = request.args.get("q", "").strip()
    f_type   = request.args.get("type", "all")
    sort_by  = request.args.get("sort", "relevance")
    results  = []
    total    = 0

    if q:
        results, total = _search(q, session["user_id"],
                                 session.get("role","user"),
                                 f_type, sort_by)

    return render_template("search.html",
                           query=q, results=results, total=total,
                           filter_type=f_type, sort_by=sort_by)


def _search(query, user_id, role, f_type, sort_by):
    conn     = get_db_connection()
    cleaned  = clean_text(query)
    score_map = {}

    try:
        # ── FTS5 BM25 search ──────────────────────────────
        if role == "admin":
            rows = conn.execute("""
                SELECT f.doc_id, bm25(fts_documents) score
                FROM fts_documents f
                JOIN documents d ON d.id=f.doc_id
                WHERE fts_documents MATCH ? AND d.is_deleted=0
                ORDER BY score
            """, (cleaned,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT f.doc_id, bm25(fts_documents) score
                FROM fts_documents f
                JOIN documents d ON d.id=f.doc_id
                WHERE fts_documents MATCH ?
                  AND d.user_id=? AND d.is_deleted=0
                ORDER BY score
            """, (cleaned, user_id)).fetchall()

        doc_ids   = [r["doc_id"] for r in rows]
        score_map = {r["doc_id"]: r["score"] for r in rows}

    except Exception:
        # ── Fallback LIKE search ──────────────────────────
        like = f"%{query}%"
        if role == "admin":
            rows = conn.execute(
                "SELECT id FROM documents WHERE extracted_text LIKE ? AND is_deleted=0",
                (like,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT id FROM documents WHERE extracted_text LIKE ? AND user_id=? AND is_deleted=0",
                (like, user_id)).fetchall()
        doc_ids = [r["id"] for r in rows]

    if not doc_ids:
        conn.close()
        return [], 0

    ph     = ",".join("?" * len(doc_ids))
    params = list(doc_ids)
    type_q = ""
    if f_type != "all":
        type_q = "AND d.file_type=?"
        params.append(f_type)

    docs = conn.execute(f"""
        SELECT d.*, m.tags FROM documents d
        LEFT JOIN metadata m ON m.doc_id=d.id
        WHERE d.id IN ({ph}) {type_q}
    """, params).fetchall()
    conn.close()

    results = []
    for doc in docs:
        results.append({
            "id":            doc["id"],
            "original_name": doc["original_name"],
            "file_type":     doc["file_type"],
            "upload_date":   doc["upload_date"],
            "file_size":     doc["file_size"],
            "tags":          doc["tags"],
            "snippet":       _snippet(doc["extracted_text"] or "", query),
            "score":         score_map.get(doc["id"], 0),
        })

    if sort_by == "relevance" and score_map:
        results.sort(key=lambda x: x["score"])
    elif sort_by == "date":
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
