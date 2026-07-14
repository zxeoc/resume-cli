"""Helper functions for Resume CLI."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.json import JSON
from rich.logging import RichHandler


console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rich output.
    
    Args:
        verbose: If True, set logging level to DEBUG.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


def print_json(data: Any, indent: int = 2) -> None:
    """Pretty-print JSON data using rich.
    
    Args:
        data: The data to print as JSON.
        indent: JSON indentation level.
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=indent)
    console.print(JSON(json_str))


def save_json_to_file(data: Any, output_path: Path) -> None:
    """Save data to a JSON file.
    
    Args:
        data: The data to save.
        output_path: Path to the output file.
        
    Raises:
        IOError: If file cannot be written.
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"[green]✓[/green] Results saved to {output_path}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to save to {output_path}: {e}")
        raise


def error_exit(message: str, code: int = 1) -> None:
    """Print error message and exit.
    
    Args:
        message: Error message to display.
        code: Exit code (default: 1).
    """
    stderr_console = Console(stderr=True)
    stderr_console.print(f"[red]Error:[/red] {message}")
    sys.exit(code)
