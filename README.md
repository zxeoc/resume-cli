# resume-cli

基于 Python 的 CLI 工具，用于自动化 **简历解析**、**信息提取** 和 **JD（职位描述）匹配评分**。

它读取本地 PDF 简历，提取原始文本，调用 LLM（如 OpenAI）进行结构化信息抽取，并依据岗位描述（JD）对简历进行多维度评分与面试问题建议，帮助 HR 和候选人快速完成简历初筛。

---

## 项目简介

| 项目 | 说明 |
|---|---|
| **语言** | Python 3.9+ |
| **定位** | 本地命令行工具，简历解析 + AI 提取 + JD 匹配评分 |
| **核心能力** | `parse` 提取文本 → `extract` 结构化信息 → `score` 匹配评分 |
| **运行方式** | 本地安装后通过 `resume-cli` 命令执行 |

---

## 技术选型

| 用途 | 库 | 说明 |
|---|---|---|
| CLI 框架 | `typer` | 声明式命令行参数、子命令与帮助信息 |
| PDF 解析 | `pypdf` | 从 PDF 各页提取纯文本 |
| AI 交互 | `openai` | 调用 OpenAI 及兼容 API，支持自定义 Base URL |
| 数据校验 | `pydantic` | 校验并结构化 LLM 返回的 JSON |
| 环境变量 | `python-dotenv` | 自动加载 `.env` 文件 |
| 测试 | `pytest` | 单元测试与 CLI 集成测试 |

> `openai` SDK 兼容绝大多数 OpenAI 兼容服务（DeepSeek、Moonshot、vLLM 等），只需配置 `OPENAI_BASE_URL` 与 `OPENAI_API_KEY`。

---

## 环境变量配置方式

项目通过 `.env` 文件管理配置，首次使用时复制模板：

```bash
cp .env.example .env
```

然后编辑 `.env`，填写你的 API Key：

```bash
# .env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，兼容服务时填写
# OPENAI_MODEL=gpt-4o-mini                     # 可选，默认模型
```

脚本运行时靠 `resume-cli`（`python-dotenv`）自动加载 `.env`。也可以不建 `.env`，直接在 shell 中导出环境变量：

```bash
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 环境变量一览

| 变量 | 说明 | 默认值 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI（或兼容）API Key | 无（必填，除非使用 `--mock`） |
| `OPENAI_BASE_URL` | 兼容 API 的 Base URL | OpenAI 官方 |
| `OPENAI_MODEL` | 使用的模型名称 | `gpt-4o-mini` |

---

## 安装方式

### 前置条件

- Python 3.9+
- 包管理器：`uv`（推荐）或 `pip`

### 使用 uv（推荐）

```bash
cd resume-cli
uv sync --extra dev        # 安装运行依赖 + 开发依赖
source .venv/bin/activate  # 激活虚拟环境
resume-cli --version       # 验证安装
```

### 使用 pip

```bash
cd resume-cli
pip install -e ".[dev]"
resume-cli --version
```

> **找不到 `resume-cli` 命令？** 说明可执行文件位于项目虚拟环境 `.venv/bin/` 而未加入 `$PATH`。执行 `source .venv/bin/activate` 激活环境即可；或在任意目录全局安装 `pip install -e /data/workspace/work/resume-cli`。

### 使用 Docker（容器化）

```bash
cd resume-cli
docker build -t resume-cli .        # 构建镜像
docker run --rm resume-cli --help   # 查看帮助
```

运行时将简历与 JD 文件挂载进容器，并传入 `.env`（含 `OPENAI_API_KEY`）：

```bash
docker run --rm \
  -v "$(pwd)/.env:/app/.env:ro" \
  -v "$(pwd)/resume.pdf:/app/resume.pdf:ro" \
  -v "$(pwd)/jd.txt:/app/jd.txt:ro" \
  resume-cli extract /app/resume.pdf

docker run --rm \
  -v "$(pwd)/.env:/app/.env:ro" \
  -v "$(pwd)/resume.pdf:/app/resume.pdf:ro" \
  -v "$(pwd)/jd.txt:/app/jd.txt:ro" \
  resume-cli score /app/resume.pdf --jd /app/jd.txt
```

> 镜像采用 **editable** 安装以保持 `prompts/` 与 `mock_data/` 的相对定位有效，因此构建时会将整个项目目录复制进镜像 `WORKDIR /app`。由于 `--mock` 不访问网络，也可在无 `.env` 情况下直接运行演示。

---

## CLI 命令说明

```
Usage: resume-cli [OPTIONS] COMMAND [ARGS]...
```

### 全局选项

| 选项 | 说明 |
|---|---|
| `--mock` | 不调用 AI，返回示例数据（用于测试/演示，不消耗额度） |
| `--output, -o <file>` | 将 JSON 结果同时保存到指定文件 |
| `--verbose, -v` | 显示进度日志 |
| `--version` | 显示版本号 |

### 子命令

| 命令 | 用法 | 说明 |
|---|---|---|
| `parse` | `resume-cli parse <pdf_path>` | 提取 PDF 简历的原始文本并打印 |
| `extract` | `resume-cli extract <pdf_path>` | 提取结构化信息（姓名、电话、邮箱、城市、教育、技能） |
| `score` | `resume-cli score <pdf_path> --jd <jd_path>` | 根据 JD 对简历评分，输出总分、维度分、评语、面试问题 |

---

## 示例输入和输出

### `parse` — 解析 PDF 文本

**输入**：`resume.pdf`（含文本层的简历 PDF）

```bash
resume-cli parse resume.pdf
```

**输出**（打印原始文本）：

```text
Zhang San
Python Developer
Email: zhangsan@example.com
Phone: 138-0000-0000
...
```

### `extract` — 提取结构化信息

**输入**：`resume.pdf`

```bash
resume-cli extract resume.pdf            # 调用 AI
resume-cli --mock extract resume.pdf     # 演示模式，返回示例数据
```

**输出**（Pretty JSON）：

```json
{
  "name": "张三",
  "phone": "13800000000",
  "email": "zhangsan@example.com",
  "city": "北京",
  "education": [
    {
      "school": "清华大学",
      "major": "计算机科学与技术",
      "degree": "本科",
      "graduation_time": "2022-06"
    }
  ],
  "skills": ["Python", "Docker", "Kubernetes"]
}
```

### `score` — 根据 JD 评分

**输入**：`resume.pdf` + `jd.txt`（纯文本岗位描述）

```bash
resume-cli score resume.pdf --jd jd.txt
```

**jd.txt 示例**：

```text
岗位职责：负责全栈应用的开发与维护。
任职要求：熟练使用 Python、Docker、Kubernetes，有 AI/大模型应用经验者优先。
```

**输出**（Pretty JSON）：

```json
{
  "overall_score": 82,
  "skill_score": 88,
  "experience_score": 80,
  "education_score": 75,
  "comment": "候选人具备较好的全栈开发基础，技能与岗位要求较匹配，但缺少明确的大模型应用经验。",
  "interview_questions": [
    "请介绍一个你主导过的全栈项目。",
    "你是否有调用大模型 API 的实际经验？"
  ]
}
```

### 组合用法：Mock + 输出到文件

```bash
resume-cli --mock --output result.json score resume.pdf --jd jd.txt
```

命令执行后，结果既打印到终端，也写入 `result.json`。

---

## 已实现功能

- [x] **`parse` 命令**：校验 PDF 文件存在性、扩展名、有效性；提取全页文本；空文本/扫描件错误处理
- [x] **`extract` 命令**：按预定义 Prompt 提取 6 类字段；Pydantic 校验 JSON；失败自动重试（最多 3 次尝试）
- [x] **`score` 命令**：读取 JD 文本（处理缺失/空文件）；输出总分、技能/经验/教育维度分、评语、面试问题
- [x] **全局 `--mock`**：跳过 AI 调用，返回示例数据，方便演示与测试
- [x] **全局 `--output`**：JSON 结果同时写入文件
- [x] **`--verbose` 日志**：基于 `logging` 的进度提示
- [x] **Pydantic 输出校验**：对 LLM 返回结构做强类型校验
- [x] **错误处理**：API 失败、超时、JSON 解析错误均优雅降级并给出清晰报错
- [x] **Markdown 代码块剥离**：兼容模型返回 ```json ... ``` 包装的情况
- [x] **自动化测试**：22 个 pytest 用例覆盖模型、解析、Prompt、Mock 数据加载、错误处理与 CLI mock 流程
- [x] **`.env` 配置**：`python-dotenv` 自动加载
- [x] **Prompt 外部化**：提示词独立存放于 `prompts/` 目录，按功能分文件管理
- [x] **Dockerfile**：容器化配置（Python 3.12 slim、editable 安装以保持数据目录定位）

---

## 已知问题或未完成内容

以下内容属于 AGENTS.md 的**可选（Bonus）**建议，尚未实现，后续可迭代补充：

- [ ] **扫描版 PDF（图片型）OCR**：`pypdf` 仅能提取文本层。对扫描件/图片型 PDF 会报"未找到文本"，如需支持需引入 OCR（如 `pytesseract` / `pdf2image`）
- [ ] **结构化输出（Structured Outputs）**：当前用 Prompt + Pydantic 校验实现，未使用 OpenAI 的 `response_format: json_schema` 官方结构化输出模式（可进一步降低解析失败率）
- [ ] **JD 文件格式**：`score` 的 JD 目前仅支持纯文本（`.txt`），不支持 `.pdf` / `.docx` 等格式
- [ ] **多模型/多 API 提供商**：已通过 `OPENAI_BASE_URL` 支持兼容服务，但未做提供商切换的抽象封装
- [ ] **导出格式**：JSON 导出已支持，未提供 CSV / Markdown / HTML 等报告格式

---

## 开发

```bash
pytest                          # 运行全部测试
uv sync --extra dev             # 同步开发依赖
```

## 项目结构

```
resume-cli/
├── resume_cli/
│   ├── __init__.py   # 包元信息
│   ├── main.py       # CLI 入口（Typer）
│   ├── parser.py     # PDF 解析逻辑
│   ├── llm.py        # AI 交互与 Prompt 加载
│   ├── models.py     # Pydantic 数据模型
│   └── utils.py      # 辅助函数（含 Mock 数据加载）
├── prompts/          # LLM 提示词模板（独立文件）
│   ├── extract.txt   # 信息提取提示词
│   ├── score.txt     # JD 匹配评分提示词
│   └── system.txt    # 系统提示词
├── mock_data/        # --mock 模式的示例数据
│   ├── extract.json  # 提取结果示例
│   └── score.json    # 评分结果示例
├── tests/
│   └── test_main.py
├── pyproject.toml
├── Dockerfile          # 容器化构建
├── .dockerignore
├── README.md
└── .env.example
```

> `prompts/` 与 `mock_data/` 位于包外根目录，运行时通过 `Path(__file__)` 相对定位，因此请保持 git 仓库内完整目录，且以 editable（`-e`）方式安装或直接在项目目录运行（Dockerfile 已按此方式处理）。

