# Resume CLI

A command-line tool for parsing PDF resumes, extracting structured data using AI, and scoring resumes against job descriptions.

## Features

- **Parse**: Extract raw text from PDF resumes
- **Extract**: Use AI to extract structured data (name, contact, education, skills)
- **Score**: Evaluate resume-job description match with multi-dimensional scoring
- **Mock Mode**: Test without API keys using built-in mock data
- **Pretty Output**: Rich terminal output with JSON formatting

## Installation

### From source

```bash
# Clone the repository
git clone <repository-url>
cd resume-cli

# Install in development mode
pip install -e ".[dev]"
```

### Using pip (when published)

```bash
pip install resume-cli
```

## Configuration

Create a `.env` file in your project root:

```bash
# Required: OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Custom API endpoint (for compatible APIs)
OPENAI_BASE_URL=https://api.openai.com/v1

# Optional: Model name (default: gpt-3.5-turbo)
OPENAI_MODEL=gpt-3.5-turbo
```

## Usage

### Parse a PDF resume

```bash
resume-cli parse path/to/resume.pdf
```

### Extract structured data

```bash
# Using real AI
resume-cli extract path/to/resume.pdf

# Using mock data (no API key required)
resume-cli extract path/to/resume.pdf --mock

# Save to file
resume-cli extract path/to/resume.pdf --output result.json
```

### Score resume against job description

```bash
# Using real AI
resume-cli score path/to/resume.pdf --jd path/to/job_description.txt

# Using mock data
resume-cli score path/to/resume.pdf --jd path/to/job_description.txt --mock

# Save to file
resume-cli score path/to/resume.pdf --jd path/to/job_description.txt --output score.json
```

### Global options

```bash
# Show version
resume-cli --version

# Enable verbose logging
resume-cli --verbose extract resume.pdf

# Show help
resume-cli --help
resume-cli parse --help
```

## Output Format

### Extract command output

```json
{
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
  "skills": ["Python", "JavaScript", "SQL", "机器学习"]
}
```

### Score command output

```json
{
  "overall_score": 85,
  "skill_score": 88,
  "experience_score": 80,
  "education_score": 90,
  "comment": "候选人具备扎实的计算机基础和丰富的开发经验，技能与岗位要求高度匹配。",
  "interview_questions": [
    "请介绍一个你主导过的全栈项目。",
    "你对大模型应用有什么实践经验？",
    "如何保证代码质量和可维护性？"
  ]
}
```

## Development

### Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=resume_cli
```

### Project Structure

```
resume-cli/
├── resume_cli/
│   ├── __init__.py      # Package metadata
│   ├── main.py          # CLI entry point (Typer)
│   ├── parser.py        # PDF parsing logic
│   ├── llm.py           # AI interaction and prompts
│   ├── models.py        # Pydantic data models
│   └── utils.py         # Helper functions
├── tests/
│   └── test_main.py     # Test suite
├── pyproject.toml       # Project configuration
├── .env.example         # Environment variables template
└── README.md            # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=resume_cli --cov-report=html
```

## Error Handling

The CLI provides clear error messages for common issues:

- **File not found**: When PDF or JD file doesn't exist
- **Invalid PDF**: When file is not a valid PDF
- **Empty content**: When PDF has no extractable text
- **API errors**: When AI service is unavailable or returns errors
- **Validation errors**: When AI response doesn't match expected format

## License

MIT
