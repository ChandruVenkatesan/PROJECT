"""
modules/extractor.py
────────────────────
Text extraction: PDF · DOCX · TXT · Images (Tesseract OCR)
Tokenisation and word-frequency map for the keyword indexer.
"""

import os
import re

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
                pix = page.get_pixmap(dpi=200)
                tmp = path + f"_p{i}.png"
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
        return "[Install Tesseract: pip install pytesseract pillow]"
    try:
        return pytesseract.image_to_string(Image.open(path), lang="eng")
    except Exception as e:
        return f"[OCR ERROR: {e}]"


# ── Tokeniser ─────────────────────────────────────────────

_STOP = {
    "the","a","an","is","it","in","on","at","to","of","and","or","for",
    "with","this","that","be","are","was","were","has","have","had","do",
    "does","did","not","no","by","as","if","so","but","from","up","its",
    "we","he","she","they","you","i","my","our","their","me","him","her",
}

def clean_text(text: str) -> str:
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

def word_frequencies(text: str) -> dict:
    freq = {}
    for w in clean_text(text).split():
        if w not in _STOP and len(w) > 2:
            freq[w] = freq.get(w, 0) + 1
    return freq
