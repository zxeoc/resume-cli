"""Pydantic models for resume data structures."""

from typing import Optional
from pydantic import BaseModel, Field


class Education(BaseModel):
    """Education information extracted from resume."""
    school: Optional[str] = Field(None, description="School name")
    major: Optional[str] = Field(None, description="Major/field of study")
    degree: Optional[str] = Field(None, description="Degree level")
    graduation_time: Optional[str] = Field(None, description="Graduation time")


class ResumeExtraction(BaseModel):
    """Structured resume data extracted by LLM."""
    name: Optional[str] = Field(None, description="Candidate name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    city: Optional[str] = Field(None, description="City/location")
    education: list[Education] = Field(default_factory=list, description="Education history")
    skills: list[str] = Field(default_factory=list, description="Skills list")


class ScoreResult(BaseModel):
    """Resume scoring result against job description."""
    overall_score: int = Field(..., ge=0, le=100, description="Overall match score (0-100)")
    skill_score: int = Field(..., ge=0, le=100, description="Skill match score (0-100)")
    experience_score: int = Field(..., ge=0, le=100, description="Experience match score (0-100)")
    education_score: int = Field(..., ge=0, le=100, description="Education match score (0-100)")
    comment: str = Field(..., description="Evaluation comment")
    interview_questions: list[str] = Field(
        default_factory=list,
        description="Suggested interview questions"
    )
