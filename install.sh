#!/usr/bin/env bash
# Create a virtual environment, install the libraries and build the demo files (macOS / Linux).
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python make_demo_data.py
echo
echo "Installation finished. Start the app with:  ./run_app.sh"
