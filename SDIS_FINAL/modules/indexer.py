"""
modules/indexer.py
──────────────────
Builds and manages the inverted keyword index + FTS5 virtual table.
Called after every upload and cleared on delete.
"""

from database.db import get_db_connection
from modules.extractor import word_frequencies, clean_text


def index_document(doc_id: int, text: str):
    """Insert keyword frequencies + FTS5 entry for a document."""
    conn = get_db_connection()
    try:
        # Clear any old index entries (safe to re-index)
        conn.execute("DELETE FROM document_index WHERE doc_id=?", (doc_id,))
        conn.execute("DELETE FROM fts_documents    WHERE doc_id=?", (doc_id,))

        # Inverted index (keyword → frequency)
        freq = word_frequencies(text)
        conn.executemany(
            "INSERT INTO document_index (doc_id, keyword, frequency) VALUES (?,?,?)",
            [(doc_id, kw, cnt) for kw, cnt in freq.items()]
        )

        # FTS5 full-text table
        conn.execute(
            "INSERT INTO fts_documents (doc_id, content) VALUES (?,?)",
            (doc_id, clean_text(text))
        )

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[INDEXER ERROR] doc {doc_id}: {e}")
    finally:
        conn.close()


def remove_index(doc_id: int):
    """Purge all index data for a deleted document."""
    conn = get_db_connection()
    conn.execute("DELETE FROM document_index WHERE doc_id=?", (doc_id,))
    conn.execute("DELETE FROM fts_documents    WHERE doc_id=?", (doc_id,))
    conn.commit()
    conn.close()


def top_keywords(doc_id: int, limit: int = 12) -> list:
    """Return top N keywords by frequency."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT keyword, frequency FROM document_index "
        "WHERE doc_id=? ORDER BY frequency DESC LIMIT ?",
        (doc_id, limit)
    ).fetchall()
    conn.close()
    return [{"keyword": r["keyword"], "frequency": r["frequency"]} for r in rows]


def index_stats(doc_id: int) -> dict:
    """Count unique terms and total word occurrences."""
    conn = get_db_connection()
    r = conn.execute(
        "SELECT COUNT(*) term_count, SUM(frequency) total_words "
        "FROM document_index WHERE doc_id=?", (doc_id,)
    ).fetchone()
    conn.close()
    return {"term_count": r["term_count"] or 0,
            "total_words": r["total_words"] or 0}


def total_indexed() -> int:
    conn = get_db_connection()
    n = conn.execute(
        "SELECT COUNT(DISTINCT doc_id) FROM document_index"
    ).fetchone()[0]
    conn.close()
    return n
