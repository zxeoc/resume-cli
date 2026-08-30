"""CLI entry point for resume-cli (built with Typer).

Commands:
    parse   - extract and print raw text from a PDF
    extract - extract structured resume data via the LLM
    score   - score a resume against a JD via the LLM

Global options:
    --mock   - return dummy data instead of calling the AI
    --output - save JSON results to a file
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .llm import LLMError, extract_resume, score_resume
from .parser import PDFError, extract_text
from .utils import (
    CLIError,
    mock_resume_data,
    mock_score_result,
    output_json,
    read_text_file,
)

app = typer.Typer(
    name="resume-cli",
    help="Automated resume parsing, info extraction and JD matching scoring.",
    add_completion=False,
)
verbose = False


def _init_logging(enabled: bool) -> None:
    logging.basicConfig(
        level=logging.INFO if enabled else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )


def _print_version() -> None:
    typer.echo(f"resume-cli {__version__}")


@app.callback(invoke_without_command=True, no_args_is_help=True)
def main(
    ctx: typer.Context,
    mock: bool = typer.Option(False, "--mock", help="Return dummy data instead of calling the AI."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save JSON result to a file."),
    verbose_flag: bool = typer.Option(False, "--verbose", "-v", help="Show progress logging."),
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    """Global options shared by all commands."""
    global verbose
    verbose = verbose_flag
    _init_logging(verbose_flag)

    if version:
        _print_version()
        raise typer.Exit()

    ctx.obj = {"mock": mock, "output": output}


def _validate_pdf_arg(pdf_path: str) -> Path:
    """Shared PDF path validation that surfaces PDFError as a CLI error."""
    return Path(pdf_path)


@app.command()
def parse(pdf_path: str = typer.Argument(..., help="Path to the PDF resume file.")) -> None:
    """Extract and print the raw text of a PDF resume."""
    try:
        text = extract_text(pdf_path)
    except PDFError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(text)


@app.command()
def extract(
    ctx: typer.Context,
    pdf_path: str = typer.Argument(..., help="Path to the PDF resume file."),
    mock: bool = typer.Option(None, "--mock", help="Return dummy data instead of calling the AI."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save JSON result to a file."),
) -> None:
    """Extract structured resume data (name, phone, email, ...) via LLM."""
    # Command-level flags override the global callback values (Typer injects the
    # shared context as the first typer.Context parameter).
    use_mock = mock if mock is not None else ctx.obj.get("mock", False)
    out_path = output if output is not None else ctx.obj.get("output")

    if use_mock:
        output_json(mock_resume_data(), out_path)
        return

    try:
        resume_text = extract_text(pdf_path)
        data = extract_resume(resume_text)
    except (PDFError, CLIError, LLMError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    output_json(data, out_path)


@app.command()
def score(
    ctx: typer.Context,
    pdf_path: str = typer.Argument(..., help="Path to the PDF resume file."),
    jd: str = typer.Option(..., "--jd", help="Path to the job description text file."),
    mock: bool = typer.Option(None, "--mock", help="Return dummy data instead of calling the AI."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save JSON result to a file."),
) -> None:
    """Score a resume against a job description (JD) via LLM."""
    use_mock = mock if mock is not None else ctx.obj.get("mock", False)
    out_path = output if output is not None else ctx.obj.get("output")

    if use_mock:
        output_json(mock_score_result(), out_path)
        return

    try:
        resume_text = extract_text(pdf_path)
        jd_text = read_text_file(jd, description="JD file")
        result = score_resume(resume_text, jd_text)
    except (PDFError, CLIError, LLMError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)

    output_json(result, out_path)


if __name__ == "__main__":
    app()
