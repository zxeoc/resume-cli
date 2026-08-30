"""LLM interaction layer: prompt loading and OpenAI API calls.

Prompts are stored as plain-text files under the prompts/ directory and loaded
at runtime. Handles API failures, timeouts, and JSON parsing errors gracefully,
and uses Pydantic to validate the returned structure.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from string import Template
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from .models import ResumeData, ScoreResult
from .utils import get_api_key, get_base_url, get_model

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_RETRIES = 2

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class LLMError(Exception):
    """Raised when an LLM call or its response validation fails."""


def load_prompt(name: str) -> Template:
    """Load a prompt template from the prompts/ directory.

    Args:
        name: Prompt file name, e.g. "extract.txt" or "score.txt".

    Returns:
        A Template with $placeholder substitution ready for use.

    Raises:
        LLMError: if the prompt file cannot be read.
    """
    path = _PROMPTS_DIR / name
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise LLMError(f"Failed to load prompt file '{path}': {exc}") from exc
    return Template(content)


def build_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template and substitute its placeholders.

    Args:
        name: Prompt file name under prompts/.
        **kwargs: Placeholder values (e.g. resume_text=..., jd_text=...).

    Returns:
        The fully rendered prompt string.

    Raises:
        LLMError: if the prompt file cannot be read or placeholders are invalid.
    """
    template = load_prompt(name)
    try:
        return template.substitute(**kwargs)
    except KeyError as exc:
        raise LLMError(f"Prompt '{name}' has unresolved placeholder: {exc}") from exc
    except ValueError as exc:
        raise LLMError(f"Invalid placeholder in prompt '{name}': {exc}") from exc


def _strip_code_fences(raw: str) -> str:
    """Remove markdown code fences (```json ... ```) if the model wraps output."""
    content = raw.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    return content


def _parse_and_validate(raw: str, model: type[T]) -> T:
    """Parse raw LLM output as JSON and validate it against a Pydantic model.

    Raises:
        LLMError: if the output is not valid JSON or fails validation.
    """
    text = _strip_code_fences(raw)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM returned invalid JSON: {exc}") from exc
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise LLMError(f"LLM response failed validation: {exc}") from exc


def _system_prompt() -> str:
    """Return the system prompt loaded from the prompts/ directory."""
    return build_prompt("system.txt")


def _complete(prompt: str, model: type[T], retries: int = MAX_RETRIES) -> T:
    """Call the LLM with `prompt`, validating the typed response.

    Retries on transient failures (network, timeout, malformed/invalid JSON)
    up to `retries` times, then raises LLMError.
    """
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url())
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            logger.info("Calling LLM (attempt %d/%d)", attempt + 1, retries + 1)
            resp = client.chat.completions.create(
                model=get_model(),
                messages=[
                    {"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            raw = (resp.choices[0].message.content or "").strip()
            if not raw:
                raise LLMError("LLM returned an empty response.")
            return _parse_and_validate(raw, model)
        except LLMError as exc:
            last_error = exc
            logger.warning("LLM error on attempt %d: %s", attempt + 1, exc)
        except Exception as exc:
            last_error = exc
            logger.warning("LLM request failed on attempt %d: %s", attempt + 1, exc)

    raise LLMError(f"LLM call failed after {retries + 1} attempts: {last_error}")


def extract_resume(resume_text: str, retries: int = MAX_RETRIES) -> ResumeData:
    """Extract structured resume data from raw text via the LLM.

    Args:
        resume_text: The raw text of the resume.
        retries: Number of retries on failure (default 2).

    Returns:
        A validated ResumeData model.

    Raises:
        LLMError: if all attempts fail.
    """
    prompt = build_prompt("extract.txt", resume_text=resume_text)
    return _complete(prompt, ResumeData, retries=retries)


def score_resume(resume_text: str, jd_text: str, retries: int = MAX_RETRIES) -> ScoreResult:
    """Score a resume against a JD via the LLM.

    Args:
        resume_text: The raw text of the resume.
        jd_text: The job description text.
        retries: Number of retries on failure (default 2).

    Returns:
        A validated ScoreResult model.

    Raises:
        LLMError: if all attempts fail.
    """
    prompt = build_prompt("score.txt", resume_text=resume_text, jd_text=jd_text)
    return _complete(prompt, ScoreResult, retries=retries)
