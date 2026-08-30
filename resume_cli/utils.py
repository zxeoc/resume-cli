"""Shared helper functions: mock data, JSON output, JD reading, env config."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

# 加载 .env 文件中的环境变量（若存在）
load_dotenv()

logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Base error raised for user-facing CLI problems."""


def read_text_file(path: str | Path, description: str = "file") -> str:
    """Read a text file, raising a descriptive CLIError if it fails.

    Args:
        path: Path to the text file.
        description: Human-readable label used in error messages.

    Returns:
        The trimmed contents of the file.

    Raises:
        CLIError: if the file is missing or empty.
    """
    p = Path(path)
    if not p.exists():
        raise CLIError(f"{description} not found: {path}")
    if not p.is_file():
        raise CLIError(f"{description} is not a file: {path}")
    try:
        content = p.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError as exc:
        raise CLIError(f"{description} is not valid UTF-8 text: {path}") from exc
    if not content:
        raise CLIError(f"{description} is empty: {path}")
    return content


def output_json(data: BaseModel | dict | list, output_path: Optional[str] = None) -> None:
    """Print data as pretty JSON, optionally also writing it to a file.

    Args:
        data: A Pydantic model, dict, or list to serialize.
        output_path: Optional file path to write the JSON to (prints to stdout
            regardless, so the user always sees the result).
    """
    payload = data.model_dump() if isinstance(data, BaseModel) else data
    pretty = json.dumps(payload, ensure_ascii=False, indent=2)
    print(pretty)

    if output_path:
        out = Path(output_path)
        out.write_text(pretty + "\n", encoding="utf-8")
        logger.info("Saved result to %s", out)


# ---------------------------------------------------------------------------
# Environment / configuration
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    """Return OPENAI_API_KEY or raise a clear error."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise CLIError(
            "OPENAI_API_KEY is not set. Add it to a .env file "
            "or export it in your shell. Example: .env.example"
        )
    return key


def get_base_url() -> Optional[str]:
    """Return OPENAI_BASE_URL if set, else None (OpenAI default)."""
    return os.getenv("OPENAI_BASE_URL") or None


def get_model() -> str:
    """Return the model name to use (overridable via env)."""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Mock data (used when --mock is set, for testing/demo without API quota)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Mock data (used when --mock is set, for testing/demo without API quota)
# Values are loaded from the mock_data/ directory next to the project root.
# ---------------------------------------------------------------------------

_MOCK_DATA_DIR = Path(__file__).resolve().parent.parent / "mock_data"


def _load_mock_json(filename: str) -> dict[str, Any]:
    """Load a mock JSON data file from the mock_data/ directory."""
    path = _MOCK_DATA_DIR / filename
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise CLIError(f"Failed to load mock data file '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise CLIError(f"Mock data file '{path}' must contain a JSON object.")
    return data


def mock_resume_data() -> dict[str, Any]:
    """Return extraction data for --mock mode, loaded from mock_data/extract.json."""
    return _load_mock_json("extract.json")


def mock_score_result() -> dict[str, Any]:
    """Return scoring data for --mock mode, loaded from mock_data/score.json."""
    return _load_mock_json("score.json")
