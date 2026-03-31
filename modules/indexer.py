"""
modules/indexer.py
──────────────────
Builds and manages the inverted keyword index in MySQL.
Uses MySQL FULLTEXT index on documents.extracted_text for search.
"""

from database.db import get_db_connection
from modules.extractor import word_frequencies


def index_document(doc_id: int, text: str):
    """Insert keyword frequencies for a document."""
    conn = get_db_connection()
    cur  = conn.cursor()
    try:
        # Clear old entries first (safe to re-index)
        cur.execute("DELETE FROM document_index WHERE doc_id=%s", (doc_id,))

        freq = word_frequencies(text)
        if freq:
            cur.executemany(
                "INSERT INTO document_index (doc_id, keyword, frequency) VALUES (%s,%s,%s)",
                [(doc_id, kw, cnt) for kw, cnt in freq.items()]
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[INDEXER ERROR] doc {doc_id}: {e}")
    finally:
        cur.close()
        conn.close()


def remove_index(doc_id: int):
    """Remove all keyword entries for a deleted document."""
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM document_index WHERE doc_id=%s", (doc_id,))
    conn.commit()
    cur.close()
    conn.close()


def top_keywords(doc_id: int, limit: int = 12) -> list:
    """Return top N keywords by frequency for a document."""
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT keyword, frequency FROM document_index "
        "WHERE doc_id=%s ORDER BY frequency DESC LIMIT %s",
        (doc_id, limit)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def index_stats(doc_id: int) -> dict:
    """Return unique term count and total word occurrences."""
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT COUNT(*) term_count, SUM(frequency) total_words "
        "FROM document_index WHERE doc_id=%s",
        (doc_id,)
    )
    r = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "term_count":  r["term_count"]  or 0,
        "total_words": r["total_words"] or 0
    }


def total_indexed() -> int:
    """Count distinct documents that have index entries."""
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT doc_id) FROM document_index")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n
