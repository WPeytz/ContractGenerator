import os, json, requests, re, unicodedata, glob
import streamlit_authenticator as stauth
from io import BytesIO
import streamlit as st
from docxtpl import DocxTemplate
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

st.set_page_config(page_title="Kontraktgenerator", layout="wide")    

# --- Autentifikation (kun adgang for teamet) ---
# Forventet struktur i Streamlit Secrets (TOML):
# [auth]
# cookie_name = "mk_contractgen"
# signature_key = "REPLACE_WITH_RANDOM_LONG_SECRET"
# cookie_expiry_days = 7
# [auth.credentials.usernames.mette]
# name = "Mette Klingsten"
# email = "mk@mklaw.dk"
# password = "$2b$12$EXAMPLE_BCRYPT_HASH"
# [auth.credentials.usernames.anna]
# name = "Anna Jensen"
# email = "anna@firma.dk"
# password = "$2b$12$ANOTHER_HASH"

def _to_plain(obj):
    # Recursively convert SecretsProxy / mappings / sequences to plain Python types
    if hasattr(obj, "items"):          # mapping-like (dict/SecretsProxy)
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [ _to_plain(v) for v in obj ]
    return obj

auth_conf = st.secrets.get("auth", {})
creds = _to_plain(auth_conf.get("credentials", {}))  # now a real dict
# Fix: allow email login by mapping emails -> credentials
def normalize_credentials(creds):
    new_creds = {"usernames": {}}
    for user, data in creds.get("usernames", {}).items():
        # Use email as the login key instead of internal username
        email = data.get("email", user)
        new_creds["usernames"][email] = data
    return new_creds
cookie_name = auth_conf.get("cookie_name", "contractgen")
signature_key = auth_conf.get("signature_key", "CHANGE_ME_SECRET")
cookie_expiry_days = auth_conf.get("cookie_expiry_days", 7)

creds = _to_plain(auth_conf.get("credentials", {}))
creds = normalize_credentials(creds)  # NEW LINE

authenticator = stauth.Authenticate(
    creds,
    cookie_name,
    signature_key,
    cookie_expiry_days
)

name, auth_status, username = authenticator.login(location="main")

if auth_status is False:
    st.error("Ugyldigt brugernavn eller adgangskode")
    st.stop()
elif auth_status is None:
    st.info("Indtast brugernavn og adgangskode for at fortsætte")
    st.stop()

# Når man er logget ind, vis logout-knap i sidepanelet
with st.sidebar:
    authenticator.logout("Log ud")

if load_dotenv:
    load_dotenv()

BASE = "https://api.app.legis365.com/public/v1.0"

# API-nøgle hentes fra Streamlit Secrets (Cloud) eller miljøvariabel (lokalt)
def has_api_key():
    return bool(st.secrets.get("LEGIS_API_KEY", "") or os.getenv("LEGIS_API_KEY", ""))

def get_headers():
    key = st.secrets.get("LEGIS_API_KEY", "") or os.getenv("LEGIS_API_KEY", "")
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
if not has_api_key():
    st.warning("Appen har ingen API-nøgle endnu. Tilføj `LEGIS_API_KEY` i Secrets (⚙️ → Secrets) for at hente data.")

with st.sidebar:
    st.subheader("Indstillinger")
    if not has_api_key():
        st.error("Mangler API-nøgle. Tilføj `LEGIS_API_KEY` i Streamlit Secrets (Cloud) eller som miljøvariabel lokalt.")

    # Find skabeloner
    template_files = sorted(glob.glob("templates/*.docx"))
    sel_template = st.selectbox(
        "Vælg skabelon (.docx)",
        options=template_files if template_files else ["<Ingen skabeloner fundet>"],
        index=0,
        disabled=not template_files,
    )
    # Init session state for data
    if "contacts" not in st.session_state:
        st.session_state.contacts = {}
    if "journals" not in st.session_state:
        st.session_state.journals = []

col1, col2 = st.columns(2)
with col1:
        if st.button("Hent seneste Kontakter & Journaler"):
            contacts_list = list(paged("/Contacts"))
            st.session_state.contacts = {c["id"]: c for c in contacts_list}
            st.session_state.journals = list(paged("/Journals"))
            json.dump(st.session_state.contacts, open("contacts.json","w"), ensure_ascii=False, indent=2)
            json.dump(st.session_state.journals, open("journals.json","w"), ensure_ascii=False, indent=2)
            st.success(f"Hentede {len(st.session_state.contacts)} kontakter og {len(st.session_state.journals)} journaler.")

contacts = st.session_state.contacts
journals = st.session_state.journals
if not contacts or not journals:
    st.info("Tryk på 'Hent seneste Kontakter & Journaler' først.")
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
        if not has_api_key():
            st.error("Manglende API-nøgle. Angiv `LEGIS_API_KEY` i Secrets (⚙️ → Secrets) eller som miljøvariabel.")
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
        if not has_api_key():
            st.error("Manglende API-nøgle. Angiv `LEGIS_API_KEY` i Secrets (⚙️ → Secrets) eller som miljøvariabel.")
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