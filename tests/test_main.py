"""Basic tests for resume-cli: models, parsing, mock mode, and CLI behavior."""

from __future__ import annotations

import json

import pytest
from pypdf import PdfWriter
from typer.testing import CliRunner

from resume_cli import models
from resume_cli.llm import build_prompt
from resume_cli.main import app
from resume_cli.parser import PDFError, extract_text, validate_pdf
from resume_cli.utils import CLIError, read_text_file

runner = CliRunner()


# ---------------------------------------------------------------------------
# Test PDF helpers
# ---------------------------------------------------------------------------

# A minimal, hand-crafted one-page PDF whose single content stream draws the
# literal text "Hello Resume". This avoids pulling in a heavy PDF-generation
# dependency (e.g. reportlab) just for tests.
_DYNAMIC_STREAM = "<< /Length {length} >>\nstream\n{content}\nendstream"
_MINIMAL_TEMPLATE = """%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
{stream}
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000247 00000 n
0000000351 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
416
%%EOF
"""


def write_test_pdf(path, text="Hello Resume"):
    """Write a minimal PDF containing `text` in its text layer."""
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
    stream = _DYNAMIC_STREAM.format(length=len(content), content=content)
    pdf = _MINIMAL_TEMPLATE.format(stream=stream)
    path.write_bytes(pdf.encode("latin-1"))
    return path


def make_pdf(tmp_path, name="resume.pdf", text="Hello Resume"):
    return write_test_pdf(tmp_path / name, text)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

def test_resume_data_valid_parsing():
    payload = {
        "name": "张三",
        "phone": "13800000000",
        "email": "a@b.com",
        "city": "北京",
        "education": [
            {"school": "清华", "major": "CS", "degree": "本科", "graduation_time": "2022-06"}
        ],
        "skills": ["Python", "Docker"],
    }
    data = models.ResumeData.model_validate(payload)
    assert data.name == "张三"
    assert data.skills == ["Python", "Docker"]
    assert len(data.education) == 1


def test_resume_data_defaults_to_empty():
    data = models.ResumeData.model_validate({})
    assert data.name is None
    assert data.education == []
    assert data.skills == []


def test_score_result_rejects_out_of_range_scores():
    payload = {
        "overall_score": 150,  # outside 0-100
        "skill_score": 80,
        "experience_score": 70,
        "education_score": 60,
        "comment": "ok",
        "interview_questions": [],
    }
    with pytest.raises(Exception):  # pydantic ValidationError
        models.ScoreResult.model_validate(payload)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_extract_text_ok(tmp_path):
    pdf = make_pdf(tmp_path, text="Hello Resume")
    assert "Hello Resume" in extract_text(pdf)


def test_extract_text_empty_pdf_raises(tmp_path):
    # A valid but content-less PDF must raise PDFError.
    empty = tmp_path / "empty.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(empty, "wb") as f:
        writer.write(f)

    with pytest.raises(PDFError):
        extract_text(empty)


def test_validate_pdf_missing_file(tmp_path):
    missing = tmp_path / "nope.pdf"
    with pytest.raises(PDFError):
        validate_pdf(missing)


def test_validate_pdf_wrong_extension(tmp_path):
    txt = tmp_path / "resume.txt"
    txt.write_text("not a pdf", encoding="utf-8")
    with pytest.raises(PDFError):
        validate_pdf(txt)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def test_extraction_prompt_contains_placeholders():
    filled = build_prompt("extract.txt", resume_text="SOME TEXT")
    assert "SOME TEXT" in filled
    assert '"name"' in filled


def test_scoring_prompt_contains_both_texts():
    filled = build_prompt("score.txt", resume_text="R", jd_text="JD")
    assert "R" in filled
    assert "JD" in filled
    assert '"overall_score"' in filled


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------

def test_read_text_file_empty_raises(tmp_path):
    f = tmp_path / "jd.txt"
    f.write_text("   \n  ", encoding="utf-8")
    with pytest.raises(CLIError):
        read_text_file(f)


def test_read_text_file_missing_raises(tmp_path):
    with pytest.raises(CLIError):
        read_text_file(tmp_path / "ghost.txt")


def test_read_text_file_ok(tmp_path):
    f = tmp_path / "jd.txt"
    f.write_text(" 要求：Python 全栈 \n", encoding="utf-8")
    assert read_text_file(f) == "要求：Python 全栈"


def test_mock_data_loaded_from_disk():
    from resume_cli import utils

    extract = utils.mock_resume_data()
    score = utils.mock_score_result()
    assert extract["name"] == "张三"
    assert extract["education"][0]["school"] == "北京大学"
    assert score["overall_score"] == 85


def test_mock_data_missing_file_raises(tmp_path, monkeypatch):
    from resume_cli import utils

    monkeypatch.setattr(utils, "_MOCK_DATA_DIR", tmp_path)
    with pytest.raises(CLIError):
        utils.mock_resume_data()


def test_mock_data_invalid_json_raises(tmp_path, monkeypatch):
    from resume_cli import utils

    monkeypatch.setattr(utils, "_MOCK_DATA_DIR", tmp_path)
    (tmp_path / "extract.json").write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(CLIError):
        utils.mock_resume_data()


# ---------------------------------------------------------------------------
# CLI (mock mode)
# ---------------------------------------------------------------------------

def test_parse_ok(tmp_path):
    pdf = make_pdf(tmp_path, text="Hello Resume")
    result = runner.invoke(app, ["parse", str(pdf)])
    assert result.exit_code == 0
    assert "Hello Resume" in result.output


def test_parse_missing_pdf(tmp_path):
    result = runner.invoke(app, ["parse", str(tmp_path / "nope.pdf")])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_extract_mock(tmp_path):
    pdf = make_pdf(tmp_path)
    result = runner.invoke(app, ["--mock", "extract", str(pdf)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "张三"
    assert data["education"][0]["school"] == "北京大学"
    assert data["skills"]


def test_score_mock(tmp_path):
    pdf = make_pdf(tmp_path)
    jd = tmp_path / "jd.txt"
    jd.write_text("岗位要求：Python 全栈开发", encoding="utf-8")
    result = runner.invoke(app, ["--mock", "score", str(pdf), "--jd", str(jd)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["overall_score"] == 85
    assert data["education_score"] == 90
    assert data["interview_questions"]


def test_score_mock_missing_jd(tmp_path):
    pdf = make_pdf(tmp_path)
    # Mock mode should not require the JD file to exist.
    result = runner.invoke(app, ["--mock", "score", str(pdf), "--jd", str(tmp_path / "ghost.txt")])
    assert result.exit_code == 0


def test_output_flag_writes_file(tmp_path):
    pdf = make_pdf(tmp_path)
    out_file = tmp_path / "out.json"
    result = runner.invoke(app, ["--mock", "--output", str(out_file), "extract", str(pdf)])
    assert result.exit_code == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["name"] == "张三"


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "resume-cli" in result.output
