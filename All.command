#!/bin/bash
set -e
cd "$(dirname "$0")"

# Ensure venv exists
if [ ! -d ".venv" ]; then
  /usr/bin/python3 -m venv .venv
  source .venv/bin/activate
  pip install -U pip
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

# Fetch fresh data and generate docs
python fetch_data.py
python generate_contracts.py

# Optional: convert to PDF if LibreOffice is installed
# find contracts -name "*.docx" -print0 | xargs -0 -I{} soffice --headless --convert-to pdf --outdir contracts "{}"

osascript -e 'display notification "Kontrakter er genereret" with title "ContractGenerator"'