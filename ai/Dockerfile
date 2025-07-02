# Use an official Python runtime as a parent image
FROM python:3.13

# Copy the uv package manager and its binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements first for better caching
COPY app/pyproject.toml .
COPY app/uv.lock .
RUN apt-get update && apt-get install -y libboost-all-dev

# Install dependencies and sync the virtual environment
RUN uv lock && \
    uv sync --locked

# Make port 8011 available to the world outside this container
RUN uv run python -m ensurepip --upgrade && \
    uv run python -m spacy download en_core_web_lg

# Copy the application code
COPY app/ .
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8011


CMD ["uv","run","main.py"]