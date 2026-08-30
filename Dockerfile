# resume-cli 容器化镜像
#
# 代码通过 Path(__file__).parent.parent 定位 prompts/ 与 mock_data/ 目录，
# 因此使用 editable 安装（-e .），使 __file__ 指向 /app/resume_cli/，
# 从而正确定位 /app/prompts 与 /app/mock_data。

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 复制项目源码与数据目录（保持目录结构完整）
COPY resume_cli ./resume_cli
COPY prompts ./prompts
COPY mock_data ./mock_data
COPY pyproject.toml README.md ./

# editable 安装，保证 prompts/ 与 mock_data/ 的相对定位有效
RUN pip install --upgrade pip && pip install -e .

# 默认入口为 resume-cli
ENTRYPOINT ["resume-cli"]
CMD ["--help"]
