# Use an official Python runtime as a parent image
FROM python:3.12

# Copy the uv package manager and its binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

## --- Dependency resolution layer ---
# Copy dependency metadata first for better caching
COPY app/pyproject.toml .
COPY app/uv.lock .

# System build deps needed for camel-kenlm (kenlm C++ build) & other libs
# - build-essential / cmake / ninja-build: compile C++ extensions
# - libboost-all-dev: required by kenlm
# - {zlib,bzip2,lzma,lz4,zstd}-dev: compression backends sometimes used
# - git, pkg-config: occasionally required by sdists
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake ninja-build git pkg-config \
    libboost-all-dev libeigen3-dev libomp-dev zlib1g-dev libbz2-dev liblzma-dev liblz4-dev libzstd-dev \
    && rm -rf /var/lib/apt/lists/*

# Workaround for CMake policy removing FindBoost behavior in newer versions used by pip 'cmake' wheels
ENV CMAKE_POLICY_DEFAULT_CMP0167=OLD
ENV BOOST_INCLUDEDIR=/usr/include \
    BOOST_LIBRARYDIR=/usr/lib/x86_64-linux-gnu

# Ensure OpenMP flags are set so camel-kenlm links correctly
ENV CFLAGS="${CFLAGS} -fopenmp" \
    CXXFLAGS="${CXXFLAGS} -fopenmp" \
    LDFLAGS="${LDFLAGS} -fopenmp"

# Sync the virtual environment from the provided lock file (no re-lock needed inside image)
RUN uv lock
RUN uv sync --locked

# Pre-download spaCy English model (can be overridden via build arg)
ARG SPACY_MODEL=en_core_web_lg
RUN uv run python -m ensurepip --upgrade && \
    uv run python -m spacy download ${SPACY_MODEL}

# Copy the application code
COPY app/ .
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8011


CMD ["uv","run","main.py"]