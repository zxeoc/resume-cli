# Resume CLI

## 项目简介

Resume CLI 是一个基于 Python 的命令行工具，用于自动化处理 PDF 简历。它能够解析 PDF 文件、利用大语言模型 (LLM) 提取结构化信息，并根据职位描述 (JD) 进行匹配度评分。

## 技术选型

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.9+ | 主要开发语言 |
| CLI 框架 | Typer | 命令行接口开发 |
| PDF 解析 | pypdf | PDF 文本提取 |
| AI SDK | openai | 兼容 OpenAI 及兼容 API |
| 数据校验 | Pydantic | JSON 数据结构校验 |
| 终端美化 | Rich | 彩色输出与格式化 |
| 测试框架 | pytest | 单元测试 |

## 环境变量配置方式

在项目根目录创建 `.env` 文件：

```bash
# 必填：OpenAI API 密钥
OPENAI_API_KEY=sk-your-api-key-here

# 可选：自定义 API 端点（兼容 OpenAI 的第三方 API）
OPENAI_BASE_URL=https://api.openai.com/v1

# 可选：模型名称（默认：gpt-3.5-turbo）
OPENAI_MODEL=gpt-3.5-turbo

# 可选：推理强度控制（仅 o1/o3/o4 系列模型生效）
# 可选值：low / medium / high
# OPENAI_REASONING_EFFORT=low
```

## 安装方式

### 从源码安装

```bash
# 克隆仓库
git clone <repository-url>
cd resume-cli

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 通过 pip 安装（发布后）

```bash
pip install resume-cli
```

## CLI 命令说明

### 全局选项

| 选项 | 说明 |
|------|------|
| `--version, -V` | 显示版本号 |
| `--help` | 显示帮助信息 |
| `--verbose, -v` | 启用详细日志 |

### parse 命令 - 解析 PDF 文本

```bash
resume-cli parse <pdf_path>
```

从 PDF 简历中提取原始文本并输出到终端。

### extract 命令 - AI 提取结构化数据

```bash
resume-cli extract <pdf_path> [--mock] [--output <file>]
```

调用 LLM 从简历中提取姓名、联系方式、教育背景、技能等信息。

### score 命令 - 简历评分

```bash
resume-cli score <pdf_path> --jd <jd_path> [--mock] [--output <file>]
```

根据职位描述对简历进行多维度评分。

### 通用选项

| 选项 | 说明 |
|------|------|
| `--mock, -m` | 使用模拟数据（无需 API 密钥） |
| `--output, -o` | 将结果保存为 JSON 文件 |

## 示例输入和输出

### 输入：示例简历 PDF

假设 `resume.pdf` 包含以下内容：

```
张三
电话：138-0000-0000
邮箱：zhangsan@example.com
城市：北京

教育背景：
北京大学 | 计算机科学与技术 | 本科 | 2020年6月

技能：Python, JavaScript, SQL, 机器学习, Docker
```

### 输入：示例 JD 文件

`job_description.txt`：

```
职位：全栈开发工程师
要求：
- 熟悉 Python、JavaScript
- 了解数据库设计
- 有 Docker 使用经验
- 了解机器学习基础知识
```

### 输出：extract 命令

```bash
resume-cli extract resume.pdf --mock
```

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

### 输出：score 命令

```bash
resume-cli score resume.pdf --jd job_description.txt --mock
```

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

## 已实现功能

- [x] PDF 简历文本解析
- [x] AI 结构化数据提取（姓名、电话、邮箱、城市、教育、技能）
- [x] 简历与 JD 匹配度评分（总分、技能、经验、教育 4 个维度）
- [x] 生成面试问题建议
- [x] 模拟模式（无需 API 即可测试）
- [x] JSON 文件导出
- [x] 彩色终端输出
- [x] 详细日志模式
- [x] 完整的错误处理（文件不存在、PDF 无效、API 失败等）
- [x] Docker 容器化支持
- [x] 单元测试（19 个测试用例）

## 已知问题或未完成内容

- [ ] 大型 PDF 文件可能导致 LLM 上下文窗口溢出，需优化文本截断策略
- [ ] 不支持扫描版 PDF（纯图片）的 OCR 识别
- [ ] 评分维度权重固定，暂不支持自定义权重配置
- [ ] 未支持批量处理多个简历文件
- [ ] 未支持从远程 URL 下载 PDF
- [ ] 中文 PDF 的文本提取可能因编码问题出现乱码
- [ ] 未添加 Python 包发布配置（PyPI 上传）