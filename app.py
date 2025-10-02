import os, json, requests, re, unicodedata, glob
import streamlit_authenticator as stauth
from io import BytesIO
import streamlit as st
from docxtpl import DocxTemplate
from pathlib import Path
import pdfplumber, re
from dateutil import parser as dparse
from dotenv import load_dotenv


def _to_plain(obj):
    # Recursively convert SecretsProxy / mappings / sequences to plain Python types
    if hasattr(obj, "items"):          # mapping-like (dict/SecretsProxy)
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [ _to_plain(v) for v in obj ]
    return obj

auth_conf = st.secrets.get("auth", {})
creds = _to_plain(auth_conf.get("credentials", {}))  # now a real dict
cookie_name = auth_conf.get("cookie_name", "contractgen")
signature_key = auth_conf.get("signature_key", "CHANGE_ME_SECRET")
cookie_expiry_days = auth_conf.get("cookie_expiry_days", 7)

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

def _clean(s): return re.sub(r'\s+', ' ', (s or '')).strip()

def extract_from_contract(pdf_path: str):
    out = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    t = _clean(text)

    # Arbejdsgiver (CVR, navn, adresse)
    m = re.search(r'CVR[\s\-:]*([0-9]{8})', t)
    if m: out['C_CoRegCVR'] = m.group(1)
    if "MBWS" in t: out['C_Name'] = "MBWS"
    # Medarbejdernavn
    m2 = re.search(r'AND\s+([A-ZÆØÅa-zæøå\s]+)\s+CPR', t)
    if m2: out['P_Name'] = m2.group(1).strip()
    # Startdato
    m3 = re.search(r'With effect from ([A-Za-z0-9,\s]+?), the Employee is employed', t)
    if m3:
        try: out['EmploymentStart'] = dparse.parse(m3.group(1)).date().isoformat()
        except: out['EmploymentStart'] = m3.group(1)
    # Løn
    m4 = re.search(r'fixed annual salary of DKK\s*([\d\.,]+)', t)
    if m4:
        annual = float(m4.group(1).replace('.','').replace(',',''))
        out['MonthlySalary'] = str(round(annual/12))
    return out

def extract_from_payslip(pdf_path: str):
    out = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    t = _clean(text)
    m = re.search(r'Fra:\s*([0-9\-\.\/]+).*?Til:\s*([0-9\-\.\/]+)', t)
    if m:
        out['PeriodFrom'] = m.group(1)
        out['PeriodTo'] = m.group(2)
    m2 = re.search(r'Fast månedsløn[^\d]*([\d\.,]+)', t)
    if m2: out['MonthlySalary'] = m2.group(1)
    return out

def build_context(contract_data, payslip_data, ui):
    return {
        "C_Name": contract_data.get("C_Name") or ui.get("C_Name"),
        "C_Address": ui.get("C_Address",""),
        "C_CoRegCVR": contract_data.get("C_CoRegCVR") or ui.get("C_CoRegCVR"),
        "P_Name": contract_data.get("P_Name") or ui.get("P_Name"),
        "P_Address": ui.get("P_Address",""),
        "MonthlySalary": payslip_data.get("MonthlySalary") or contract_data.get("MonthlySalary"),
        "EmploymentStart": contract_data.get("EmploymentStart") or ui.get("EmploymentStart"),
        "TerminationDate": ui.get("TerminationDate"),
        "SeparationDate": ui.get("SeparationDate"),
        "GardenLeaveStart": ui.get("GardenLeaveStart"),
    }

# --- NY SEKTIONS-UI ---
st.header("Auto-udfyld Fratrædelsesaftale")

c1, c2 = st.columns(2)
with c1:
    contract_file = st.file_uploader("Upload ansættelseskontrakt (PDF)", type=["pdf"], key="contract")
with c2:
    payslip_file = st.file_uploader("Upload lønseddel (PDF)", type=["pdf"], key="payslip")

auto = {}
if contract_file:
    tmp = "/tmp/contract.pdf"; open(tmp,"wb").write(contract_file.read())
    auto.update(extract_from_contract(tmp))
if payslip_file:
    tmp2 = "/tmp/payslip.pdf"; open(tmp2,"wb").write(payslip_file.read())
    auto.update(extract_from_payslip(tmp2))

st.subheader("Ret/tilføj oplysninger")
ui_ctx = {}
ui_ctx["C_Name"] = st.text_input("Arbejdsgiver", auto.get("C_Name",""))
ui_ctx["C_Address"] = st.text_input("Arbejdsgiver adresse", "")
ui_ctx["C_CoRegCVR"] = st.text_input("CVR", auto.get("C_CoRegCVR",""))
ui_ctx["P_Name"] = st.text_input("Medarbejder", auto.get("P_Name",""))
ui_ctx["P_Address"] = st.text_input("Medarbejder adresse", "")
ui_ctx["MonthlySalary"] = st.text_input("Månedsløn (DKK)", auto.get("MonthlySalary",""))
ui_ctx["EmploymentStart"] = st.text_input("Ansættelsesstart", auto.get("EmploymentStart",""))
ui_ctx["TerminationDate"] = st.text_input("Opsigelsesdato")
ui_ctx["SeparationDate"] = st.text_input("Fratrædelsesdato")
ui_ctx["GardenLeaveStart"] = st.text_input("Fritstilling fra")

if st.button("Generér Fratrædelsesaftale"):
    ctx = build_context(auto, auto, ui_ctx)
    tpl = "templates/Fratrædelsesaftale - DA.docx"
    if not Path(tpl).exists():
        st.error("Skabelon ikke fundet: templates/Fratrædelsesaftale - DA.docx")
    else:
        doc = DocxTemplate(tpl)
        doc.render(ctx)
        bio = BytesIO(); doc.docx.save(bio); bio.seek(0)
        st.download_button("Download aftale", bio,
            file_name=f"Fratraedelsesaftale_{safe_slug(ctx['P_Name'])}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

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