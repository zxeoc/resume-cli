"""AI interaction and prompt templates for resume processing."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from openai import OpenAI
from pydantic import ValidationError

from .models import ResumeExtraction, ScoreResult, Education

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    prompt_file = PROMPTS_DIR / f"{name}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


def get_llm_client() -> OpenAI:
    """Initialize and return an OpenAI client.
    
    Returns:
        OpenAI client instance.
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    base_url = os.getenv("OPENAI_BASE_URL")
    
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    
    return OpenAI(**client_kwargs)


def call_llm(prompt: str, client: Optional[OpenAI] = None) -> str:
    """Call the LLM API with a prompt.
    
    Args:
        prompt: The prompt to send to the LLM.
        client: Optional pre-configured OpenAI client.
        
    Returns:
        The LLM response text.
        
    Raises:
        RuntimeError: If the API call fails.
    """
    if client is None:
        client = get_llm_client()
    
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    call_kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 5000,
        "response_format": {"type": "json_object"}
    }
    
    reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT")
    if reasoning_effort and model.startswith(("o1", "o3", "o4")):
        call_kwargs["reasoning_effort"] = reasoning_effort
    
    try:
        response = client.chat.completions.create(**call_kwargs)
        
        content = response.choices[0].message.content
        
        if content is None:
            raise RuntimeError("LLM returned empty response")
        
        return content.strip()
        
    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}")


def extract_resume_data(resume_text: str, client: Optional[OpenAI] = None) -> ResumeExtraction:
    """Extract structured data from resume text using LLM.
    
    Args:
        resume_text: The raw resume text.
        client: Optional pre-configured OpenAI client.
        
    Returns:
        Structured resume data.
        
    Raises:
        RuntimeError: If extraction fails.
    """
    prompt_template = load_prompt("extract")
    prompt = prompt_template.format(resume_text=resume_text)
    response = call_llm(prompt, client)
    
    try:
        data = json.loads(response)
        return ResumeExtraction(**data)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
    except ValidationError as e:
        raise RuntimeError(f"LLM response does not match expected schema: {e}")


def score_resume(resume_text: str, jd_text: str, client: Optional[OpenAI] = None) -> ScoreResult:
    """Score a resume against a job description using LLM.
    
    Args:
        resume_text: The raw resume text.
        jd_text: The job description text.
        client: Optional pre-configured OpenAI client.
        
    Returns:
        Scoring result with scores and feedback.
        
    Raises:
        RuntimeError: If scoring fails.
    """
    prompt_template = load_prompt("score")
    prompt = prompt_template.format(resume_text=resume_text, jd_text=jd_text)
    response = call_llm(prompt, client)
    
    try:
        data = json.loads(response)
        return ScoreResult(**data)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
    except ValidationError as e:
        raise RuntimeError(f"LLM response does not match expected schema: {e}")
