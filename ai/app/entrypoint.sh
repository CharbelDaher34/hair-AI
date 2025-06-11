#!/usr/bin/env bash
set -e           # exit immediately if any command fails
uv sync
uv run python -m ensurepip --upgrade
uv run python -m spacy download en_core_web_lg


# 2) Start the main application
exec uv run main.py