"""
modules/extractor.py
────────────────────
Cloud-compatible text extraction:
  - PDF      → PyMuPDF  (digital text layer)
  - DOCX     → python-docx
  - TXT      → plain read
  - Images   → OCR.space free API  (no Tesseract install needed)
  - Scanned PDF → each page rendered as image → OCR.space API

Set OCR_SPACE_API_KEY in your .env file.
Free tier: 25,000 requests/month  →  https://ocr.space/ocrapi/freekey
"""

import os
import re
import base64
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import fitz
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    from docx import Document as DocxDoc
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

OCR_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "helloworld")
OCR_API_URL = "https://api.ocr.space/parse/image"


def extract_text(file_path: str, ext: str) -> str:
    ext = ext.lower().strip(".")
    if ext == "txt":
        return _from_txt(file_path)
    elif ext == "pdf":
        return _from_pdf(file_path)
    elif ext == "docx":
        return _from_docx(file_path)
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp", "gif", "webp"):
        return _from_image_api(file_path)
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
            txt = page.get_text("text").strip()
            if txt:
                pages.append(txt)
            else:
                pix  = page.get_pixmap(dpi=150)
                tmp  = path + f"_page{i}.png"
                pix.save(tmp)
                ocr_text = _from_image_api(tmp)
                pages.append(ocr_text)
                try:
                    os.remove(tmp)
                except Exception:
                    pass
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


def _from_image_api(path: str) -> str:
    try:
        with open(path, "rb") as f:
            img_data = f.read()

        ext = path.rsplit(".", 1)[-1].lower()
        mime_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png",  "gif": "image/gif",
            "bmp": "image/bmp",  "tiff": "image/tiff",
            "webp": "image/webp"
        }
        mime = mime_map.get(ext, "image/png")
        b64  = base64.b64encode(img_data).decode("utf-8")

        payload = {
            "apikey":            OCR_API_KEY,
            "base64Image":       f"data:{mime};base64,{b64}",
            "language":          "eng",
            "isOverlayRequired": False,
            "detectOrientation": True,
            "scale":             True,
            "OCREngine":         2,
        }

        response = requests.post(OCR_API_URL, data=payload, timeout=30)
        result   = response.json()

        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage", ["Unknown error"])
            if "invalid api key" in str(error_msg).lower():
                return "[OCR ERROR: Invalid API key. Get free key at ocr.space/ocrapi/freekey]"
            return f"[OCR API ERROR: {error_msg}]"

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return "[OCR: No text found in image]"

        texts = [r.get("ParsedText", "") for r in parsed_results]
        return "\n".join(t for t in texts if t.strip())

    except requests.exceptions.Timeout:
        return "[OCR ERROR: API request timed out. Try again.]"
    except requests.exceptions.ConnectionError:
        return "[OCR ERROR: Could not connect to OCR.space API.]"
    except Exception as e:
        return _fallback_tesseract(path) or f"[OCR ERROR: {e}]"


def _fallback_tesseract(path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        possible = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(possible):
            pytesseract.pytesseract.tesseract_cmd = possible
        return pytesseract.image_to_string(Image.open(path), lang="eng")
    except Exception:
        return ""


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