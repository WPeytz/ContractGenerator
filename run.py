#!/usr/bin/env python3
import os, sys, subprocess, platform, shutil, venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQ = ROOT / "requirements.txt"

PY_EXE = None

def ensure_venv():
    global PY_EXE
    if not VENV_DIR.exists():
        print("Creating virtual environment .venv ...")
        venv.EnvBuilder(with_pip=True).create(str(VENV_DIR))

    if platform.system() == "Windows":
        PY_EXE = VENV_DIR / "Scripts" / "python.exe"
        PIP_EXE = VENV_DIR / "Scripts" / "pip.exe"
    else:
        PY_EXE = VENV_DIR / "bin" / "python3"
        PIP_EXE = VENV_DIR / "bin" / "pip"

    # Install requirements if needed
    if not REQ.exists():
        (ROOT / "requirements.txt").write_text(
            "docxtpl==0.20.1\nrequests>=2.31\npython-dotenv>=1.0\n"
        )
    print("Upgrading pip and installing requirements ...")
    # Upgrade pip (use long flag for compatibility) and install requirements
    try:
        subprocess.check_call([str(PIP_EXE), "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        # Fallback: use `python -m pip` if direct pip call fails
        subprocess.check_call([str(PY_EXE), "-m", "pip", "install", "--upgrade", "pip"])

    try:
        subprocess.check_call([str(PIP_EXE), "install", "-r", str(REQ)])
    except subprocess.CalledProcessError:
        subprocess.check_call([str(PY_EXE), "-m", "pip", "install", "-r", str(REQ)])

def run(pyfile):
    print(f"Running {pyfile} ...")
    subprocess.check_call([str(PY_EXE), str(ROOT / pyfile)])

def notify_ok():
    if platform.system() == "Darwin":
        # macOS notification
        try:
            subprocess.call([
                "osascript", "-e",
                'display notification "Kontrakter er genereret" with title "ContractGenerator"'
            ])
        except Exception:
            pass

def main():
    os.chdir(ROOT)
    ensure_venv()

    # Ensure output folder exists
    (ROOT / "contracts").mkdir(exist_ok=True)
    (ROOT / "templates").mkdir(exist_ok=True)

    # Fetch latest data & generate contracts
    run("fetch_data.py")
    run("generate_contracts.py")

    print("\n✅ Done. Contracts saved in:", (ROOT / "contracts").resolve())
    notify_ok()

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running step: {e}")
        sys.exit(e.returncode)