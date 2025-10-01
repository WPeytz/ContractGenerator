import os, json, requests, re, unicodedata, glob
from io import BytesIO
import streamlit as st
from docxtpl import DocxTemplate
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

BASE = "https://api.app.legis365.com/public/v1.0"

# API nøgle i session (enten fra .env eller fra input)
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("LEGIS_API_KEY", "")

def get_headers():
    key = st.session_state.api_key or os.getenv("LEGIS_API_KEY", "")
    return {"Accept": "application/json", "X-API-Key": key}

def safe_slug(s, n=120):
    if not s: return "Uden_navn"
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r'[\\/\\n\\r:*?"<>|]', "_", s)
    s = re.sub(r"\\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9._-]", "_", s)
    return re.sub(r"_+", "_", s).strip("_.")[:n] or "Uden_navn"

def paged(path, page_size=500):
    page=1
    while True:
        r = requests.get(BASE+path, headers=get_headers(), params={"page":page,"pageSize":page_size}, timeout=60)
        r.raise_for_status()
        data=r.json(); items=data.get("results") or []
        if not items: break
        for it in items: yield it
        if len(items) < page_size: break
        page+=1

st.set_page_config(page_title="Kontraktgenerator", layout="wide")
st.title("Kontraktgenerator")

# Sidebar: API nøgle + skabelonvalg
with st.sidebar:
    st.subheader("Indstillinger")
    st.text_input("API nøgle", type="password", key="api_key",
                  help="Gemmes kun i denne session. Brug helst LEGIS_API_KEY i en .env-fil.")

    # Find skabeloner
    template_files = sorted(glob.glob("templates/*.docx"))
    sel_template = st.selectbox(
        "Vælg skabelon (.docx)",
        options=template_files if template_files else ["<Ingen skabeloner fundet>"],
        index=0,
        disabled=not template_files,
    )

col1, col2 = st.columns(2)
with col1:
    if st.button("Hent seneste Kontakter & Journaler"):
        contacts=list(paged("/Contacts")); journals=list(paged("/Journals"))
        json.dump(contacts, open("contacts.json","w"), ensure_ascii=False, indent=2)
        json.dump(journals, open("journals.json","w"), ensure_ascii=False, indent=2)
        st.success(f"Hentede {len(contacts)} kontakter og {len(journals)} journaler.")

contacts = {c["id"]: c for c in json.load(open("contacts.json"))} if Path("contacts.json").exists() else {}
journals = json.load(open("journals.json")) if Path("journals.json").exists() else []
st.write(f"Indlæst {len(contacts)} kontakter, {len(journals)} journaler.")

query = st.text_input("Søg i journaler (navn/nummer):")
view = [j for j in journals if (query.lower() in (j.get('name') or '').lower()) or (query.lower() in (j.get('number') or '').lower())]
sel = st.multiselect("Vælg journaler", options=[f"{j.get('number')} — {j.get('name')}" for j in view])

OUT = Path("contracts"); OUT.mkdir(exist_ok=True)

def generate_for(j, template_path: str):
    c = contacts.get(j.get("clientId"))
    if not c:
        return None, None, "Ingen klient"
    if not template_path or not Path(template_path).exists():
        return None, None, "Skabelon ikke fundet"

    ctx = {"client": c, "journal": j}

    # Gem til disk
    doc = DocxTemplate(template_path)
    doc.render(ctx)
    base = f"{safe_slug(j.get('number') or 'IngenNummer')}_{safe_slug(c.get('name') or 'UkendtKlient')}"
    filename = OUT / f"{base}.docx"
    doc.save(filename)

    # Kopi i hukommelsen til download
    bio = BytesIO()
    doc2 = DocxTemplate(template_path)
    doc2.render(ctx)
    doc2.docx.save(bio)
    bio.seek(0)

    return filename.name, bio, None

colA, colB = st.columns(2)
with colA:
    if st.button("Generér for valgte"):
        if not st.session_state.api_key:
            st.error("Manglende API nøgle. Tilføj i sidepanelet eller i .env-filen")
        elif not glob.glob("templates/*.docx"):
            st.error("Ingen skabeloner fundet i templates/-mappen.")
        else:
            count = 0
            generated = []
            by_num = {j.get('number'): j for j in journals}
            for label in sel:
                num = label.split(" — ", 1)[0]
                j = by_num.get(num)
                if not j:
                    continue
                try:
                    fname, buf, err = generate_for(j, sel_template)
                    if err:
                        st.error(f"{num}: {err}")
                    else:
                        generated.append((num, fname, buf))
                        count += 1
                except Exception as e:
                    st.error(f"{num}: {e}")
            st.success(f"Genereret {count} fil(er) i contracts/")
            for num, fname, buf in generated:
                st.download_button(
                    label=f"Hent {fname}",
                    data=buf,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

with colB:
    if st.button("Generér ALLE journaler"):
        if not st.session_state.api_key:
            st.error("Manglende API nøgle. Tilføj i sidepanelet eller i .env-filen")
        elif not glob.glob("templates/*.docx"):
            st.error("Ingen skabeloner fundet i templates/-mappen.")
        else:
            count = 0
            generated = []
            for j in journals:
                try:
                    fname, buf, err = generate_for(j, sel_template)
                    if err:
                        st.error(f"{j.get('number')}: {err}")
                    else:
                        generated.append((j.get('number'), fname, buf))
                        count += 1
                except Exception as e:
                    st.error(f"{j.get('number')}: {e}")
            st.success(f"Genereret {count} fil(er) i contracts/")
            for num, fname, buf in generated[:10]:
                st.download_button(
                    label=f"Hent {fname}",
                    data=buf,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            if len(generated) > 10:
                st.info(f"Viser de første 10 downloads her. Alle filer er gemt i: {OUT.resolve()}")