"""Pydantic models for validating and structuring LLM output.

These models mirror the JSON structures required by the prompts defined in
AGENTS.md. Validation failures are surfaced clearly so callers can retry or
report a graceful error instead of crashing on malformed AI output.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Education(BaseModel):
    """A single education entry extracted from a resume."""

    school: Optional[str] = Field(default=None, description="学校名称")
    major: Optional[str] = Field(default=None, description="专业")
    degree: Optional[str] = Field(default=None, description="学历")
    graduation_time: Optional[str] = Field(default=None, description="毕业时间")


class ResumeData(BaseModel):
    """Structured personal and professional data extracted from a resume."""

    name: Optional[str] = Field(default=None, description="姓名")
    phone: Optional[str] = Field(default=None, description="电话")
    email: Optional[str] = Field(default=None, description="邮箱")
    city: Optional[str] = Field(default=None, description="所在城市")
    education: List[Education] = Field(default_factory=list, description="教育经历列表")
    skills: List[str] = Field(default_factory=list, description="技能列表")


class ScoreResult(BaseModel):
    """Scoring result evaluating a resume against a JD."""

    overall_score: int = Field(ge=0, le=100, description="总分 (0-100)")
    skill_score: int = Field(ge=0, le=100, description="技能分数")
    experience_score: int = Field(ge=0, le=100, description="经验分数")
    education_score: int = Field(ge=0, le=100, description="教育分数")
    comment: str = Field(default="", description="评语")
    interview_questions: List[str] = Field(default_factory=list, description="建议的面试问题")
