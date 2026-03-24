"""
modules/extractor.py
────────────────────
Text extraction from: PDF · DOCX · TXT · Images (OCR)
Tokenization and word-frequency map for the indexer.
"""

import os
import re

# ── Optional lib imports ──────────────────────────────────
try:
    import pytesseract
    from PIL import Image
    OCR_OK = True
except ImportError:
    OCR_OK = False

try:
    import fitz          # PyMuPDF
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    from docx import Document as DocxDoc
    DOCX_OK = True
except ImportError:
    DOCX_OK = False


# ── Main dispatcher ───────────────────────────────────────

def extract_text(file_path: str, ext: str) -> str:
    """Route to correct extractor based on file extension."""
    ext = ext.lower().strip(".")
    if ext == "txt":
        return _from_txt(file_path)
    elif ext == "pdf":
        return _from_pdf(file_path)
    elif ext == "docx":
        return _from_docx(file_path)
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp"):
        return _from_image(file_path)
    return ""


def _from_txt(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[TXT ERROR: {e}]"


def _from_pdf(path):
    if not PDF_OK:
        return "[Install PyMuPDF: pip install pymupdf]"
    try:
        doc   = fitz.open(path)
        pages = []
        for i, page in enumerate(doc):
            txt = page.get_text("text")
            if txt.strip():
                pages.append(txt)
            elif OCR_OK:
                pix  = page.get_pixmap(dpi=200)
                tmp  = path + f"_p{i}.png"
                pix.save(tmp)
                pages.append(_from_image(tmp))
                os.remove(tmp)
        doc.close()
        return "\n".join(pages)
    except Exception as e:
        return f"[PDF ERROR: {e}]"


def _from_docx(path):
    if not DOCX_OK:
        return "[Install python-docx: pip install python-docx]"
    try:
        doc = DocxDoc(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"[DOCX ERROR: {e}]"


def _from_image(path):
    if not OCR_OK:
        return "[Install Tesseract + pillow: pip install pytesseract pillow]"
    try:
        return pytesseract.image_to_string(Image.open(path), lang="eng")
    except Exception as e:
        return f"[OCR ERROR: {e}]"


# ── Tokenizer / frequency map ─────────────────────────────

_STOP = {
    "the","a","an","is","it","in","on","at","to","of","and","or","for",
    "with","this","that","be","are","was","were","has","have","had","do",
    "does","did","not","no","by","as","if","so","but","from","up","its",
    "we","he","she","they","you","i","my","our","their","its","me","him",
    "her","us","them","who","what","when","where","how","all","any","each",
}

def clean_text(text: str) -> str:
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

def tokenize(text: str) -> list:
    return [w for w in clean_text(text).split()
            if w not in _STOP and len(w) > 2]

def word_frequencies(text: str) -> dict:
    freq = {}
    for w in tokenize(text):
        freq[w] = freq.get(w, 0) + 1
    return freq
