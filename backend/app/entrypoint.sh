#!/usr/bin/env bash
set -e           # exit immediately if any command fails

uv run scripts/create_tables.py

# 2) Start the main application
exec uv run main.py