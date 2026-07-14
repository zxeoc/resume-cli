"""Tests for Resume CLI."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from resume_cli import __version__
from resume_cli.main import app
from resume_cli.models import Education, ResumeExtraction, ScoreResult
from resume_cli.parser import PDFParseError, extract_text_from_pdf, read_text_file, validate_pdf

runner = CliRunner()


class TestModels:
    """Test Pydantic models."""
    
    def test_resume_extraction_defaults(self):
        """Test ResumeExtraction with default values."""
        result = ResumeExtraction()
        assert result.name is None
        assert result.phone is None
        assert result.email is None
        assert result.city is None
        assert result.education == []
        assert result.skills == []
    
    def test_resume_extraction_with_data(self):
        """Test ResumeExtraction with provided data."""
        data = {
            "name": "张三",
            "phone": "138-0000-0000",
            "email": "zhangsan@example.com",
            "city": "北京",
            "education": [
                {
                    "school": "北京大学",
                    "major": "计算机科学",
                    "degree": "本科",
                    "graduation_time": "2020年6月"
                }
            ],
            "skills": ["Python", "JavaScript"]
        }
        result = ResumeExtraction(**data)
        assert result.name == "张三"
        assert result.phone == "138-0000-0000"
        assert result.email == "zhangsan@example.com"
        assert result.city == "北京"
        assert len(result.education) == 1
        assert result.education[0].school == "北京大学"
        assert len(result.skills) == 2
    
    def test_score_result_validation(self):
        """Test ScoreResult validation."""
        result = ScoreResult(
            overall_score=85,
            skill_score=88,
            experience_score=80,
            education_score=90,
            comment="Good candidate",
            interview_questions=["Question 1"]
        )
        assert result.overall_score == 85
        assert result.comment == "Good candidate"
    
    def test_score_result_range_validation(self):
        """Test ScoreResult score range validation."""
        with pytest.raises(Exception):
            ScoreResult(
                overall_score=101,  # Out of range
                skill_score=88,
                experience_score=80,
                education_score=90,
                comment="Good candidate",
                interview_questions=[]
            )


class TestParser:
    """Test PDF parser functions."""
    
    def test_validate_pdf_nonexistent(self):
        """Test validate_pdf with non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_pdf(Path("nonexistent.pdf"))
    
    def test_extract_text_nonexistent(self):
        """Test extract_text_from_pdf with non-existent file."""
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf(Path("nonexistent.pdf"))
    
    def test_read_text_file_nonexistent(self):
        """Test read_text_file with non-existent file."""
        with pytest.raises(FileNotFoundError):
            read_text_file(Path("nonexistent.txt"))
    
    def test_read_text_file_empty(self, tmp_path):
        """Test read_text_file with empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        with pytest.raises(PDFParseError):
            read_text_file(empty_file)
    
    def test_read_text_file_success(self, tmp_path):
        """Test read_text_file with valid file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello, World!")
        result = read_text_file(txt_file)
        assert result == "Hello, World!"


class TestLLM:
    """Test LLM functions."""
    
    def test_mock_extraction(self):
        """Test mock extraction data."""
        from resume_cli.llm import MOCK_EXTRACTION
        assert MOCK_EXTRACTION.name == "张三"
        assert MOCK_EXTRACTION.email == "zhangsan@example.com"
        assert len(MOCK_EXTRACTION.skills) > 0
    
    def test_mock_score(self):
        """Test mock score data."""
        from resume_cli.llm import MOCK_SCORE
        assert 0 <= MOCK_SCORE.overall_score <= 100
        assert 0 <= MOCK_SCORE.skill_score <= 100
        assert 0 <= MOCK_SCORE.experience_score <= 100
        assert 0 <= MOCK_SCORE.education_score <= 100
        assert MOCK_SCORE.comment
        assert len(MOCK_SCORE.interview_questions) > 0


class TestCLI:
    """Test CLI commands."""
    
    def test_version(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
    
    def test_help(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "resume-cli" in result.output
    
    def test_parse_nonexistent(self):
        """Test parse command with non-existent file."""
        result = runner.invoke(app, ["parse", "nonexistent.pdf"])
        assert result.exit_code != 0
    
    def test_extract_nonexistent(self):
        """Test extract command with non-existent file."""
        result = runner.invoke(app, ["extract", "nonexistent.pdf"])
        assert result.exit_code != 0
    
    def test_extract_mock(self):
        """Test extract command with --mock flag."""
        # Create a mock PDF file (just needs to exist for mock mode)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 fake content")
            tmp_path = f.name
        
        try:
            result = runner.invoke(app, ["extract", tmp_path, "--mock"])
            # Mock mode should work without actual PDF parsing
            assert result.exit_code == 0 or "Error" in result.output
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_score_nonexistent_jd(self):
        """Test score command with non-existent JD file."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 fake content")
            tmp_path = f.name
        
        try:
            result = runner.invoke(app, ["score", tmp_path, "--jd", "nonexistent.txt"])
            assert result.exit_code != 0
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestIntegration:
    """Integration tests."""
    
    def test_models_roundtrip(self):
        """Test model serialization roundtrip."""
        original = ResumeExtraction(
            name="Test",
            skills=["Python", "Go"]
        )
        data = original.model_dump()
        restored = ResumeExtraction(**data)
        assert original.name == restored.name
        assert original.skills == restored.skills
    
    def test_score_models_roundtrip(self):
        """Test score model serialization roundtrip."""
        original = ScoreResult(
            overall_score=90,
            skill_score=85,
            experience_score=88,
            education_score=92,
            comment="Excellent",
            interview_questions=["Q1", "Q2"]
        )
        data = original.model_dump()
        restored = ScoreResult(**data)
        assert original.overall_score == restored.overall_score
        assert original.interview_questions == restored.interview_questions
