"""
PDF extractor and text normalizer for course plans.
Handles digital PDFs (pypdf/pdfplumber) and provides graceful fallback
with informative error messages for scanned PDFs without a text layer.
"""
import os
import re
import json
from typing import Dict, List, Any, Optional

try:
    import pypdf
except ImportError:
    pypdf = None


def clean_text_markers(text: str) -> str:
    """
    Strips markers like (T1), (T2), *, [Ref Text Book 1], [Ref...],
    (Theory), (ref Text Book 2), extra whitespaces, etc.
    """
    if not text:
        return ""
    # Strip references like [Ref Text Book 1] or [Ref...] or [anything in square brackets]
    cleaned = re.sub(r"\[Ref[^\]]*\]", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    # Strip tutorial markers like (T1), (T12), (t5)
    cleaned = re.sub(r"\([Tt]\d+\)", "", cleaned)
    # Strip asterisks
    cleaned = re.sub(r"\*+", "", cleaned)
    # Strip theory/tutorial indicators in parentheses
    cleaned = re.sub(r"\(Theory\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(ref\s+Text\s+Book\s+\d+\)", "", cleaned, flags=re.IGNORECASE)
    # Clean up redundant spaces and trailing punctuation
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:,\t\r\n")
    return cleaned


def merge_continued_rows(topics_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merges rows that indicate CONTINUED topics into the preceding topic row.
    Skips lecture 0 entirely.
    """
    merged: List[Dict[str, Any]] = []
    for item in topics_raw:
        lec_num = item.get("lecture_num")
        # Rule: skip lecture 0
        if str(lec_num).strip() in ("0", "L0", "0(T0)"):
            continue

        raw_name = item.get("name", "").strip()
        cleaned_name = clean_text_markers(raw_name)

        is_continued = bool(
            re.search(r"\bCONTINUED\b", raw_name, flags=re.IGNORECASE)
            or re.search(r"–\s*CONTINUED", raw_name, flags=re.IGNORECASE)
        )

        if is_continued and merged:
            # Merge with previous topic
            base_cleaned = re.sub(r"[–-]?\s*CONTINUED.*$", "", cleaned_name, flags=re.IGNORECASE).strip(" -:,")
            if base_cleaned and base_cleaned not in merged[-1]["name"]:
                merged[-1]["name"] += f" (Part 2: {base_cleaned})"
            merged[-1]["continued"] = True
            if "hours" in item and "hours" in merged[-1]:
                try:
                    merged[-1]["hours"] += float(item["hours"])
                except (ValueError, TypeError):
                    pass
        else:
            item_copy = dict(item)
            item_copy["name"] = cleaned_name
            merged.append(item_copy)

    return merged


def extract_pdf_course_plan(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts course plan content from a PDF file.
    If the PDF is a scan without a text layer, raises a clear RuntimeError
    explaining that an OCR engine / vision model is needed.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pypdf is None:
        raise ImportError("pypdf is required to extract PDF text.")

    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    text_per_page = [page.extract_text() or "" for page in reader.pages]
    total_text_length = sum(len(t.strip()) for t in text_per_page)

    if total_text_length == 0:
        raise RuntimeError(
            f"Scanned PDF without text layer detected for: {os.path.basename(pdf_path)} "
            f"({total_pages} scanned pages). "
            "To extract scanned PDFs, install an OCR engine (e.g., Tesseract OCR via pytesseract) "
            "or run through a vision-capable multimodal pipeline. "
            "Pre-extracted verified seed JSONs are available in backend/seed/."
        )

    full_text = "\n".join(text_per_page)
    return {
        "file_name": os.path.basename(pdf_path),
        "total_pages": total_pages,
        "full_text": full_text,
    }
