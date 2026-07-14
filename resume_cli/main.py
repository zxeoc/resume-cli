"""CLI entry point for Resume CLI."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

from .llm import extract_resume_data, score_resume
from .models import ResumeExtraction, ScoreResult
from .parser import PDFParseError, extract_text_from_pdf, read_text_file
from .utils import (
    console,
    error_exit,
    print_json,
    save_json_to_file,
    setup_logging,
)

# Load environment variables
load_dotenv()

MOCK_DATA_DIR = Path(__file__).parent.parent / "mock_data"

# Create Typer app
app = typer.Typer(
    name="resume-cli",
    help="CLI tool for resume parsing, extraction, and JD matching.",
    no_args_is_help=True,
)

# Global options
mock_option = typer.Option(
    False,
    "--mock",
    "-m",
    help="Use mock data instead of calling AI API (for testing/demo)."
)
output_option = typer.Option(
    None,
    "--output",
    "-o",
    help="Save output to a JSON file."
)
verbose_option = typer.Option(
    False,
    "--verbose",
    "-v",
    help="Enable verbose logging."
)


def load_mock_data(name: str) -> dict:
    """Load mock data from JSON file."""
    mock_file = MOCK_DATA_DIR / f"{name}.json"
    if not mock_file.exists():
        raise FileNotFoundError(f"Mock data file not found: {mock_file}")
    return json.loads(mock_file.read_text(encoding="utf-8"))


def get_mock_extraction() -> ResumeExtraction:
    """Get mock extraction data from file."""
    return ResumeExtraction(**load_mock_data("extract"))


def get_mock_score() -> ScoreResult:
    """Get mock score data from file."""
    return ScoreResult(**load_mock_data("score"))


@app.command()
def parse(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF resume file."),
    verbose: bool = verbose_option,
    output: Optional[Path] = output_option,
) -> None:
    """Parse a PDF resume and extract raw text.
    
    Extracts text content from all pages of a PDF file and prints it to stdout.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Parsing PDF: {pdf_path}")
    
    try:
        text = extract_text_from_pdf(pdf_path)
        
        console.print("\n[bold cyan]Extracted Text:[/bold cyan]\n")
        console.print(text)
        
        if output:
            save_json_to_file({"text": text}, output)
        
    except FileNotFoundError as e:
        error_exit(str(e))
    except PDFParseError as e:
        error_exit(str(e))
    except Exception as e:
        error_exit(f"Unexpected error: {e}")


@app.command()
def extract(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF resume file."),
    mock: bool = mock_option,
    verbose: bool = verbose_option,
    output: Optional[Path] = output_option,
) -> None:
    """Extract structured data from a resume using AI.
    
    Parses the PDF and uses LLM to extract key information like name, contact,
    education, and skills into a structured JSON format.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Extracting data from: {pdf_path}")
    
    try:
        # Parse PDF text
        text = extract_text_from_pdf(pdf_path)
        
        if mock:
            logger.info("Using mock data")
            result = get_mock_extraction()
        else:
            logger.info("Calling LLM API for extraction...")
            result = extract_resume_data(text)
        
        console.print("\n[bold cyan]Extracted Data:[/bold cyan]\n")
        print_json(result.model_dump())
        
        if output:
            save_json_to_file(result.model_dump(), output)
        
    except FileNotFoundError as e:
        error_exit(str(e))
    except PDFParseError as e:
        error_exit(str(e))
    except ValueError as e:
        error_exit(str(e))
    except RuntimeError as e:
        error_exit(f"AI extraction failed: {e}")
    except Exception as e:
        error_exit(f"Unexpected error: {e}")


@app.command()
def score(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF resume file."),
    jd_path: Path = typer.Option(..., "--jd", "-j", help="Path to the job description file."),
    mock: bool = mock_option,
    verbose: bool = verbose_option,
    output: Optional[Path] = output_option,
) -> None:
    """Score a resume against a job description using AI.
    
    Evaluates how well a candidate's resume matches a job description and
    provides scores across multiple dimensions with feedback.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Scoring resume: {pdf_path}")
    logger.info(f"Against JD: {jd_path}")
    
    try:
        # Parse PDF text
        resume_text = extract_text_from_pdf(pdf_path)
        
        # Read JD text
        jd_text = read_text_file(jd_path)
        
        if mock:
            logger.info("Using mock data")
            result = get_mock_score()
        else:
            logger.info("Calling LLM API for scoring...")
            result = score_resume(resume_text, jd_text)
        
        console.print("\n[bold cyan]Score Result:[/bold cyan]\n")
        print_json(result.model_dump())
        
        if output:
            save_json_to_file(result.model_dump(), output)
        
    except FileNotFoundError as e:
        error_exit(str(e))
    except PDFParseError as e:
        error_exit(str(e))
    except ValueError as e:
        error_exit(str(e))
    except RuntimeError as e:
        error_exit(f"AI scoring failed: {e}")
    except Exception as e:
        error_exit(f"Unexpected error: {e}")


@app.callback(invoke_without_command=True)
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version and exit.",
        is_eager=True,
    ),
) -> None:
    """Resume CLI - A tool for parsing, extracting, and scoring resumes."""
    if version:
        from . import __version__
        console.print(f"resume-cli version {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
