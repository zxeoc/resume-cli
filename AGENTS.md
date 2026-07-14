# Agent: Resume CLI Builder

## Role
你是一个资深的全栈工程师，擅长构建高效的命令行 (CLI) 工具和集成 AI 能力。你的目标是创建一个名为 `resume-cli` 的 Python 工具，用于自动化简历解析、信息提取和 JD 匹配评分。

## Project Overview
构建一个基于 Python 的 CLI 工具，能够读取本地 PDF 简历，利用 LLM (如 OpenAI) 进行结构化数据提取，并根据职位描述 (JD) 进行匹配度评分。该工具需要具备良好的工程结构、错误处理和用户体验。

## Tech Stack
- **Language**: Python 3.9+
- **CLI Framework**: `Typer` (推荐) or `Click`
- **PDF Processing**: `pypdf` or `pdfplumber`
- **AI SDK**: `openai` (compatible with OpenAI-compatible APIs)
- **Data Validation**: `Pydantic` (用于校验 AI 返回的 JSON)
- **Testing**: `pytest`

## Key Functional Requirements

### 1. Global Setup
- Initialize a Python project with `pyproject.toml`.
- Manage dependencies: `typer`, `openai`, `pypdf`, `pydantic`, `python-dotenv`.
- Support `.env` file for `OPENAI_API_KEY` configuration.

### 2. Command: `parse`
**Usage**: `resume-cli parse <pdf_path>`
- **Input**: Path to a PDF file.
- **Logic**:
  - Check if file exists.
  - Check if file is a valid PDF.
  - Extract text from all pages.
  - Handle empty text errors.
- **Output**: Print the extracted raw text to stdout.

### 3. Command: `extract`
**Usage**: `resume-cli extract <pdf_path>`
- **Logic**:
  - Parse PDF text.
  - Construct a prompt for the LLM to extract specific fields (name, phone, email, city, education, skills).
  - Call LLM API.
  - **Validation**: Use Pydantic to validate the returned JSON structure. If invalid, retry or return a clear error.
  - **Error Handling**: Handle API failures, timeouts, or JSON parsing errors gracefully.
- **Output**: Pretty-printed JSON of the structured data.

### 4. Command: `score`
**Usage**: `resume-cli score <pdf_path> --jd <jd_path>`
- **Logic**:
  - Parse PDF text.
  - Read JD text file (handle file missing/empty errors).
  - Construct a prompt asking LLM to evaluate the resume against the JD.
  - Request specific score fields (overall, skill, experience, education), a comment, and interview questions.
  - Validate response format.
- **Output**: Pretty-printed JSON containing the score and feedback.

## Bonus Features (Optional but Recommended)
- Implement a global `--mock` flag. If set, return dummy data instead of calling the AI (useful for testing/demo without API quota).
- Implement `--output <filename>` flag to save JSON results to a file.
- Add simple logging (e.g., using `logging` module) to show progress.
- Create a `Dockerfile` for containerization.

## Project Structure
Create a clean structure similar to this:
```
resume-cli/
├── resume_cli/
│ ├── init.py
│ ├── main.py # CLI entry point
│ ├── parser.py # PDF parsing logic
│ ├── llm.py # AI interaction and prompts
│ ├── models.py # Pydantic models
│ └── utils.py # Helper functions
├── tests/
│ └── test_main.py
├── pyproject.toml
├── README.md
└── .env.example
```
## Implementation Prompts for AI Logic
### Extraction Prompt Template
```text
请从以下简历文本中提取关键信息，并以严格的 JSON 格式返回。不要包含 Markdown 代码块标记 (如 ```json)，只返回纯 JSON 字符串。
如果某个字段无法找到，请使用 null 或空列表。

简历内容：
{resume_text}

JSON 结构要求：
{
"name": "姓名",
"phone": "电话",
"email": "邮箱",
"city": "所在城市",
"education": [
{
"school": "学校",
"major": "专业",
"degree": "学历",
"graduation_time": "毕业时间"
}
],
"skills": ["技能1", "技能2"]
}
```
### Scoring Prompt Template
```text
你是一个专业的 HR 和技术面试官。请根据以下岗位描述 (JD) 对候选人的简历进行评分。

简历内容：
{resume_text}

岗位描述 (JD)：
{jd_text}

请以 JSON 格式返回评分结果（0-100分），包含总分、各维度分、评语及建议的面试问题。不要包含 Markdown 代码块标记，只返回纯 JSON 字符串。

JSON 结构要求：
{
"overall_score": 82,
"skill_score": 88,
"experience_score": 80,
"education_score": 75,
"comment": "简要评价…",
"interview_questions": ["问题1", "问题2"]
}
```
## Execution Steps
1. Set up the project structure and dependencies.
2. Implement the `models.py` with Pydantic classes.
3. Implement the `parser.py` for PDF text extraction.
4. Implement the `llm.py` with functions for extraction and scoring (incorporating the prompts above).
5. Implement the CLI commands in `main.py` using Typer.
6. Add error handling and `--mock` logic.
7. Write a basic test and update README.md.