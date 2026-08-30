"""PDF text extraction helpers.

Uses pypdf to read text from every page of a PDF. Raises descriptive errors
for common failure modes (missing file, not a valid PDF, empty content) so
the CLI layer can turn them into friendly messages.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


class PDFError(Exception):
    """Base exception for PDF parsing problems."""


def validate_pdf(path: Path) -> None:
    """Validate that a file exists and is a readable PDF.

    Raises:
        PDFError: if the file is missing or not a valid PDF.
    """
    if not path.exists():
        raise PDFError(f"File not found: {path}")
    if not path.is_file():
        raise PDFError(f"Path is not a file: {path}")
    if path.suffix.lower() != ".pdf":
        raise PDFError(f"Not a PDF file (expected .pdf extension): {path}")


def extract_text(pdf_path: str | Path) -> str:
    """Extract text from all pages of a PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        The concatenated raw text of all pages.

    Raises:
        PDFError: if the PDF cannot be opened/read or contains no text.
    """
    path = Path(pdf_path)
    validate_pdf(path)

    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # pypdf raises various exceptions on corrupt files
        raise PDFError(f"Failed to open PDF '{path}': {exc}") from exc

    parts: list[str] = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # a single bad page should not abort everything
            raise PDFError(f"Failed to extract text from page {page_num} of '{path}': {exc}") from exc
        parts.append(text)

    text = "\n\n".join(parts).strip()
    if not text:
        raise PDFError(f"No text found in PDF '{path}'. The file may be a scanned/image-based PDF.")

    return text
