# Use an official Python runtime as a parent image
FROM python:3.13

# Copy the uv package manager and its binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY app/pyproject.toml .
COPY app/uv.lock .

# Install dependencies and sync the virtual environment
RUN uv lock && \
    uv sync --locked

# Copy the application code
COPY app/ .
ENV PATH="/app/.venv/bin:$PATH"

# Make port 8017 available to the world outside this container
EXPOSE 8017

# CMD ["/bin/bash", "-c", "uv run scripts/create_tables.py && uv run main.py"]
CMD ["uv", "run", "main.py"]