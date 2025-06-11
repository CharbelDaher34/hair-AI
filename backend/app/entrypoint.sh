#!/usr/bin/env bash
set -e           # exit immediately if any command fails

source .venv/bin/activate
python scripts/create_tables.py

# 2) Start the main application
python main.py