"""PDF parsing logic for resume text extraction."""

import sys
from pathlib import Path
from typing import Optional

from pypdf import PdfReader


class PDFParseError(Exception):
    """Custom exception for PDF parsing errors."""
    pass


def validate_pdf(file_path: Path) -> bool:
    """Validate that the file is a valid PDF.
    
    Args:
        file_path: Path to the file to validate.
        
    Returns:
        True if valid PDF, False otherwise.
        
    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            return header == b"%PDF-"
    except Exception as e:
        raise PDFParseError(f"Error reading file: {e}")


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from all pages of a PDF file.
    
    Args:
        file_path: Path to the PDF file.
        
    Returns:
        Extracted text from all pages combined.
        
    Raises:
        FileNotFoundError: If file does not exist.
        PDFParseError: If file is not a valid PDF or cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not validate_pdf(file_path):
        raise PDFParseError(f"Not a valid PDF file: {file_path}")
    
    try:
        reader = PdfReader(file_path)
        
        if len(reader.pages) == 0:
            raise PDFParseError("PDF file has no pages")
        
        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        full_text = "\n\n".join(text_parts).strip()
        
        if not full_text:
            raise PDFParseError("PDF file contains no extractable text")
        
        return full_text
        
    except PDFParseError:
        raise
    except Exception as e:
        raise PDFParseError(f"Error extracting text from PDF: {e}")


def read_text_file(file_path: Path) -> str:
    """Read content from a text file.
    
    Args:
        file_path: Path to the text file.
        
    Returns:
        Content of the text file.
        
    Raises:
        FileNotFoundError: If file does not exist.
        PDFParseError: If file is empty or cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        content = file_path.read_text(encoding="utf-8").strip()
        
        if not content:
            raise PDFParseError(f"Text file is empty: {file_path}")
        
        return content
    except PDFParseError:
        raise
    except Exception as e:
        raise PDFParseError(f"Error reading text file: {e}")
