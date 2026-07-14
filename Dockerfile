FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY resume_cli/ resume_cli/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
ENTRYPOINT ["resume-cli"]
CMD ["--help"]
