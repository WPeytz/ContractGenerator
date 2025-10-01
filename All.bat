@echo off
cd %~dp0

REM Ensure venv exists
if not exist .venv (
    py -3 -m venv .venv
    call .venv\Scripts\activate
    pip install -U pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

REM Fetch fresh data and generate docs
python fetch_data.py
python generate_contracts.py

REM Optional: convert to PDF if LibreOffice is installed
REM for %%f in (contracts\*.docx) do soffice --headless --convert-to pdf --outdir contracts "%%f"

echo Kontrakter er genereret!
pause