# Use an official Python runtime as a parent image
FROM python:3.13

# Copy the uv package manager and its binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements first for better caching
COPY app/pyproject.toml .

# Install dependencies and ensure they're in PATH
RUN uv lock
RUN uv sync --locked
# Copy the application code
COPY app/ .
ENV PATH="/app/.venv/bin:$PATH"

# Make port 8011 available to the world outside this container
EXPOSE 8011
RUN uv run python -m ensurepip --upgrade && \
    uv run python -m spacy download en_core_web_lg

CMD ["uv","run","main.py"]