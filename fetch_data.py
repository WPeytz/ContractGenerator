import os, json, requests
from dotenv import load_dotenv

load_dotenv()
BASE = "https://api.app.legis365.com/public/v1.0"
KEY  = os.getenv("LEGIS_API_KEY")
HDRS = {"Accept": "application/json", "X-API-Key": KEY}

def paged(path, page_size=500):
    page = 1
    while True:
        r = requests.get(f"{BASE}{path}", headers=HDRS, params={"page":page,"pageSize":page_size}, timeout=60)
        r.raise_for_status()
        data = r.json()
        items = data.get("results") or data.get("items") or []
        if not items: break
        for it in items: yield it
        if len(items) < page_size: break
        page += 1

def dump(path, out_file):
    items = list(paged(path))
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(items)} -> {out_file}")

if __name__ == "__main__":
    dump("/Contacts", "contacts.json")
    dump("/Journals", "journals.json")