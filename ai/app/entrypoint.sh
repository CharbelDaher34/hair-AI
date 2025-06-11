#!/usr/bin/env bash
set -e           # exit immediately if any command fails
uv sync



# 2) Start the main application
exec uv run main.py