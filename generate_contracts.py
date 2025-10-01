import json
from docxtpl import DocxTemplate
from pathlib import Path
import re
import unicodedata

def safe_slug(value: str, maxlen: int = 120) -> str:
    """Filesystem-safe slug for filenames (macOS/Windows/Linux)."""
    if not value:
        return "Untitled"
    # Normalize unicode (e.g., æøå) to a safe form
    value = unicodedata.normalize("NFKD", value)
    # Replace forbidden characters across OSes + line breaks
    value = re.sub(r'[\\/\\n\\r:*?"<>|]', "_", value)
    # Collapse whitespace to underscores
    value = re.sub(r"\\s+", "_", value)
    # Remove anything not alnum, dot, dash, underscore
    value = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    # Collapse multiple underscores and trim dots/underscores from ends
    value = re.sub(r"_+", "_", value).strip("_.")
    # Enforce max length
    return value[:maxlen] or "Untitled"

# Load data
contacts = {c["id"]: c for c in json.load(open("contacts.json", encoding="utf-8"))}
journals = json.load(open("journals.json", encoding="utf-8"))

# Template
TEMPLATE = Path("templates/contract_template.docx")
OUT_DIR = Path("contracts")
OUT_DIR.mkdir(exist_ok=True)

for j in journals:
    client = contacts.get(j.get("clientId"))   # <-- vigtigt: lille "c"
    if not client:
        print("No client found for journal", j.get("number"))
        continue

    # Context for Word template
    ctx = {"client": client, "journal": j}

    doc = DocxTemplate(TEMPLATE)
    try:
        doc.render(ctx)
        client_name = client.get("name") or "UnknownClient"
        base = f"{safe_slug(j.get('number') or 'NoNumber')}_{safe_slug(client_name)}"
        filename = OUT_DIR / f"{base}.docx"
        doc.save(filename)
        print("Generated", filename)
    except Exception as e:
        print(f"Failed to generate for journal {j.get('number')}: {e}")

print(f"\nDone. Contracts saved in {OUT_DIR.resolve()}")