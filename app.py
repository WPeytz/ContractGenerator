import os, json, requests, re, unicodedata, glob
import streamlit_authenticator as stauth
from io import BytesIO
import streamlit as st
from docxtpl import DocxTemplate
from pathlib import Path
import pdfplumber
from dateutil import parser as dparse
from dotenv import load_dotenv
import locale
try:
    locale.setlocale(locale.LC_ALL, "da_DK.UTF-8")
except locale.Error:
    pass  # fallback if locale isn't available

load_dotenv()

st.set_page_config(page_title="Kontraktgenerator", layout="wide")

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

st.title("Kontraktgenerator")
if not has_api_key():
    st.warning("Appen har ingen API-nøgle endnu. Tilføj `LEGIS_API_KEY` i Secrets (⚙️ → Secrets) for at hente data.")

with st.sidebar:
    st.subheader("Indstillinger")
    if not has_api_key():
        st.error("Mangler API-nøgle. Tilføj `LEGIS_API_KEY` i Streamlit Secrets (Cloud) eller som miljøvariabel lokalt.")

# Ensure session state keys exist before use
if "contacts" not in st.session_state:
    st.session_state["contacts"] = {}
if "journals" not in st.session_state:
    st.session_state["journals"] = []

# --- Helpers (DK parsing) ---
DK_POSTAL = r"\b[0-9]{4}\b"

def _clean(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()

def parse_dk_amount(s: str):
    """Parse '36.500,00' or '36,500.00' or '36500' to canonical '36500.00' string."""
    if not s:
        return ""
    s = s.strip().replace(' ', '')
    # European format (comma decimals) or mixed
    if re.search(r'\d,\d{1,2}$', s) or (',' in s and '.' in s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '')
    m = re.search(r'[-+]?\d+(?:\.\d+)?', s)
    return m.group(0) if m else ""

def parse_dk_date(s: str):
    try:
        return dparse.parse(s, dayfirst=True, fuzzy=True).date().isoformat()
    except Exception:
        return s

def extract_from_contract(pdf_path: str):
    """Parse employer/employee blocks anchored on CVR and CPR to handle multi-column PDFs."""
    out = {}
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    full = "\n".join(pages)

    if show_debug:
        st.expander("Kontrakt: rå tekst").text(full[:20000])

    lines = [l.strip() for l in full.splitlines()]
    lines = [l for l in lines if l is not None]

    # --- Employer by CVR anchor ---
    cvr_idx = next((i for i, l in enumerate(lines) if re.search(r"\bCVR\b\s*:?\s*\d{8}", l, re.I)), None)
    if cvr_idx is not None:
        m = re.search(r"\bCVR\b\s*:?\s*(\d{8})", lines[cvr_idx], re.I)
        if m:
            out["C_CoRegCVR"] = m.group(1)

        window = [l for l in lines[max(0, cvr_idx-3):cvr_idx] if l]
        if window:
            # strip BETWEEN/AND from employer name line
            name_line = re.sub(r'^(BETWEEN|AND)\s+', '', window[0], flags=re.I).strip()
            out["C_Name"] = name_line

            addr_parts = [w for w in window[1:] if w]
            for j, w in enumerate(addr_parts):
                if re.search(DK_POSTAL, w):
                    addr_parts = addr_parts[:j+1]
                    break
            if addr_parts:
                out["C_Address"] = _clean(" ".join(addr_parts))

    # --- Employee by CPR anchor ---
    cpr_idx = next((i for i, l in enumerate(lines)
                    if re.search(r"\bCPR\b\s*:?$", l, re.I) or re.search(r"\bCPR\b\s*:", l, re.I)), None)
    if cpr_idx is not None:
        window = [l for l in lines[max(0, cpr_idx-4):cpr_idx] if l]
        if window:
            # Name = last line without digits (strip AND/BETWEEN if present)
            name_line = None
            for w in reversed(window):
                if not re.search(r"\d", w):
                    name_line = re.sub(r'^(BETWEEN|AND)\s+', '', w, flags=re.I).strip()
                    break
            if name_line:
                out["P_Name"] = _clean(name_line)

            # Address: prefer a postal-code line + the street line above it
            postal_idx = None
            for i, w in enumerate(window):
                if re.search(DK_POSTAL, w):
                    postal_idx = i
                    break
            if postal_idx is not None:
                street = window[postal_idx-1].strip() if postal_idx-1 >= 0 else ""
                postal = window[postal_idx].strip()
                out["P_Address"] = _clean(f"{street} {postal}".strip())
            else:
                # Fallback: last line with any digits
                addr_candidates = [w for w in window if re.search(r"\d", w)]
                if addr_candidates:
                    out["P_Address"] = _clean(addr_candidates[-1])
    else:
        # Fallback if no CPR line: use block after 'AND'
        m_and = re.search(r"\bAND\b\s*(.+)$", full, re.I | re.M)
        if m_and:
            tail = [t.strip() for t in m_and.group(1).splitlines() if t.strip()]
            if tail:
                out.setdefault("P_Name", tail[0])
            for t in tail[1:4]:
                if re.search(DK_POSTAL, t):
                    out.setdefault("P_Address", _clean(t))
                    break

    # Employment start (unchanged)
    m3 = re.search(r"With effect from ([A-Za-z0-9,\.\-\/\s]+?),\s*the Employee is employed", full, re.I)
    if m3:
        out["EmploymentStart"] = parse_dk_date(m3.group(1))

    # Salary: only when clearly labeled (guards against '3.sal' etc.)
    patterns = [
    r"fixed\s+annual\s+salary\s+of\s+(?:DKK|kr\.?)[\s]*([\d\.,]+)",
    r"(?:gross\s+)?monthly\s+salary\s+(?:is|of)\s+(?:DKK|kr\.?)[\s]*([\d\.,]+)",
    r"(?:base|fixed)?\s*salary\s*(?:is|of|amounts\s*to)\s*(?:DKK|kr\.?)?\s*([\d\.,]+)\s*(?:per\s*month|pr\.\s*måned|monthly)",
    r"\bmånedsløn\b[^\d]*([\d\.,]+)",
    r"\bårsløn\b[^\d]*([\d\.,]+)"
    ]
    monthly = None
    for pat in patterns:
        m4 = re.search(pat, full, re.I)
        if not m4:
            continue
        amt = parse_dk_amount(m4.group(1))
        try:
            if 'årsløn' in pat or 'annual' in pat:
                monthly = float(amt) / 12.0
            else:
                monthly = float(amt)
            break
        except Exception:
            pass

    if monthly is not None and monthly > 5000:
        out["MonthlySalary"] = f"{monthly:.2f}".rstrip('0').rstrip('.')

    # --- Bonus info (optional) ---
    # Try year patterns: "bonusåret 2025", "bonus for 2025", "bonus year 2025"
    m_by = re.search(r'\bbonus(?:året|year)?\s*(?:for\s*)?(20\d{2})\b', full, re.I)
    if m_by:
        out["BonusYear"] = m_by.group(1)

    # Try amount patterns: "bonus på 50.000 kr", "bonus of DKK 50,000.00"
    m_ba = re.search(r'bonus\s*(?:på|of)?\s*(?:DKK|kr\.?)?\s*([\d\.\,]+)', full, re.I)
    if m_ba:
        val = parse_dk_amount(m_ba.group(1))
        if val:
            out["BonusAmount"] = val

        # --- Clause references (optional) ---
    # Try to detect clause numbers for IP (immaterielle rettigheder) and confidentiality (tavshedspligt)
    # Patterns handle forms like:
    #  - "12. Confidentiality"
    #  - "Section 12 - Confidentiality"
    #  - "pkt. 12 Tavshedspligt"
    #  - "clause 10 on intellectual property"
    m_conf = re.search(r'(?:(?:Section|Pkt\.?|Punkt)\s*)?(\d{1,2}(?:\.\d+)*)\s*[\.-)]?\s*(Confidentiality|Tavshedspligt)', full, re.I)
    if m_conf and not out.get("ConfidentialityClauseRef"):
        out["ConfidentialityClauseRef"] = m_conf.group(1)

    m_ip = re.search(r'(?:(?:Section|Pkt\.?|Punkt)\s*)?(\d{1,2}(?:\.\d+)*)\s*[\.-)]?\s*(Intellectual\s*Property|Immaterielle\s*rettigheder)', full, re.I)
    if m_ip and not out.get("EmploymentClauseRef"):
        out["EmploymentClauseRef"] = m_ip.group(1)

    # Fallbacks like "clause 10 on confidentiality" / "pkt. 10 om immaterielle rettigheder"
    if not out.get("ConfidentialityClauseRef"):
        m = re.search(r'(?:clause|pkt\.?|punkt)\s*(\d+(?:\.\d+)*)\s*(?:om|on)?\s*(?:confidentiality|tavshedspligt)', full, re.I)
        if m:
            out["ConfidentialityClauseRef"] = m.group(1)

    if not out.get("EmploymentClauseRef"):
        m = re.search(r'(?:clause|pkt\.?|punkt)\s*(\d+(?:\.\d+)*)\s*(?:om|on)?\s*(?:intellectual\s*property|immaterielle\s*rettigheder)', full, re.I)
        if m:
            out["EmploymentClauseRef"] = m.group(1)        

    return out

def extract_from_payslip(pdf_path: str):
    out = {}
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    full = "\n".join(pages)
    t = _clean(full)

    if show_debug:
        st.expander("Lønseddel: rå tekst").text(full[:20000])

    # Period
    m = re.search(r'\bFra:\s*([0-9\-\.\/]+).*?\bTil:\s*([0-9\-\.\/]+)', full, re.I | re.S)
    if m:
        out['PeriodFrom'] = parse_dk_date(m.group(1))
        out['PeriodTo']   = parse_dk_date(m.group(2))

    # Prefer obvious monthly-salary labels; ignore hour-like amounts ~160.xx
    labels = [
        r'Fast\s*månedsløn', r'Månedsløn', r'Brutto\s*månedsløn',
        r'Fast\s*løn', r'Løn\s*\(måned\)'
    ]
    for lab in labels:
        m2 = re.search(lab + r'[^\d]*([\d\.,]+)', t, re.I)
        if not m2:
            continue
        val = parse_dk_amount(m2.group(1))
        try:
            num = float(val)
        except Exception:
            continue
        # Heuristic: monthly salaries are usually > 5,000 DKK
        if num > 5000:
            out['MonthlySalary'] = f"{num:.2f}".rstrip('0').rstrip('.')
            break
    
    # Fallback: pick the highest plausible amount on a line mentioning "løn"
    if 'MonthlySalary' not in out:
        salary_candidates = []
        for mline in re.finditer(r'(?i)l[øo]n[^\n\r]{0,40}?([\d\.,]+)', full):
            val = parse_dk_amount(mline.group(1))
            try:
                num = float(val)
                # Heuristic range for monthly salary in DKK
                if 5000 < num < 300000:
                    salary_candidates.append(num)
            except Exception:
                pass
        if salary_candidates:
            best = max(salary_candidates)
            out['MonthlySalary'] = f"{best:.2f}".rstrip('0').rstrip('.')

    # Employee name if present
    m3 = re.search(r'\bNavn\b\s*:\s*([^\n\r]+)', full, re.I)
    if m3:
        out['P_Name'] = _clean(m3.group(1))

    # --- Bonus on payslip (optional) ---
    # Grab the largest positive amount next to a 'bonus' label
    bonus_candidates = []
    for m in re.finditer(r'bonus[^\n\r]*?([\d\.,]+)', full, re.I):
        val = parse_dk_amount(m.group(1))
        try:
            num = float(val)
            if num > 0:
                bonus_candidates.append(num)
        except Exception:
            pass
    if bonus_candidates:
        best = max(bonus_candidates)
        out['BonusAmount'] = f"{best:.2f}".rstrip('0').rstrip('.')

    # Heuristic bonus year from period or explicit mention
    m_year = re.search(r'\bbonus(?:året|year)?\s*(?:for\s*)?(20\d{2})\b', full, re.I)
    if not m_year:
        # fall back: use "Til:" year if there is a period
        til = out.get('PeriodTo') or out.get('PeriodFrom')
        if til and re.match(r'\d{4}-\d{2}-\d{2}', til):
            m_year = re.match(r'(\d{4})', til)
    if m_year:
        out['BonusYear'] = m_year.group(1) if hasattr(m_year, "group") else m_year

    return out

def format_currency(val):
    """Format numeric string to Danish style e.g. 36.500,00"""
    try:
        num = float(val)
        return locale.format_string("%'.2f", num, grouping=True) \
                     .replace(".", "X").replace(",", ".").replace("X", ",")
    except Exception:
        return val or ""

def build_context(contract_data, payslip_data, ui):
    sal = payslip_data.get("MonthlySalary") or contract_data.get("MonthlySalary") or ui.get("MonthlySalary")
    norm_sal = parse_dk_amount(sal) or sal
    # Pretty-format bonus amount for Danish output (only if bonus is enabled)
    bonus_enabled = ui.get("BonusEligible")
    by = ui.get("BonusYear") if bonus_enabled else ""
    ba_raw = ui.get("BonusAmount") if bonus_enabled else ""
    ba_norm = parse_dk_amount(ba_raw) if ba_raw else ""
    ba_fmt = format_currency(ba_norm) if ba_norm else ""
    return {
        "C_Name": contract_data.get("C_Name") or ui.get("C_Name"),
        "C_Address": ui.get("C_Address", ""),
        "C_CoRegCVR": contract_data.get("C_CoRegCVR") or ui.get("C_CoRegCVR"),
        "P_Name": contract_data.get("P_Name") or ui.get("P_Name"),
        "P_Address": ui.get("P_Address", ""),
        "MonthlySalary": format_currency(norm_sal) if norm_sal else "",
        "BonusYear": by,
        "BonusAmount": ba_raw,
        "BonusAmountFmt": ba_fmt,
        # LTI (optional)
        "LTIEligible": ui.get("LTIEligible"),
        "LTIProgramName": ui.get("LTIProgramName"),
        "LTIGoodLeaver": ui.get("LTIGoodLeaver"),
        "LTISavingShareName": ui.get("LTISavingShareName"),
        "LTIMatchingShareName": ui.get("LTIMatchingShareName"),
        "EmploymentStart": contract_data.get("EmploymentStart") or ui.get("EmploymentStart"),
        "TerminationDate": ui.get("TerminationDate"),
        "SeparationDate": ui.get("SeparationDate"),
        "GardenLeaveStart": ui.get("GardenLeaveStart"),
        "AccrualMonth": ui.get("AccrualMonth"),
        "AccrualYear": ui.get("AccrualYear"),
        "HealthInsuranceIncluded": ui.get("HealthInsuranceIncluded"),
        "PensionIncluded": ui.get("PensionIncluded"),
        "LunchSchemeIncluded": ui.get("LunchSchemeIncluded"),
        "PhoneTransferIncluded": ui.get("PhoneTransferIncluded"),
        "PhoneNumber": ui.get("PhoneNumber"),
        "ManagerName": ui.get("ManagerName"),
        "EmploymentClauseRef": contract_data.get("EmploymentClauseRef") or ui.get("EmploymentClauseRef"),
        "ConfidentialityClauseRef": contract_data.get("ConfidentialityClauseRef") or ui.get("ConfidentialityClauseRef"),
        "GroupName": ui.get("GroupName"),
        "SignatureDeadline": ui.get("SignatureDeadline"),
        "SignatureMonth": ui.get("SignatureMonth"),
        "SignatureYear": ui.get("SignatureYear"),
        "RepName": ui.get("RepName"),
        "RepTitle": ui.get("RepTitle"),
        "AccruedVacationDays": ui.get("AccruedVacationDays"),
        "VacationFundName": ui.get("VacationFundName"),
        "BonusEligible": ui.get("BonusEligible"),
        "MobileCompIncluded": ui.get("MobileCompIncluded"),
        "MobileCompAmount": ui.get("MobileCompAmount"),
        "MobileCompStartDate": ui.get("MobileCompStartDate"),
    }

# --- NY SEKTIONS-UI ---
st.header("Auto-udfyld Fratrædelsesaftale")

# Show raw PDF text if you need to tune patterns
show_debug = st.checkbox("Vis rå PDF-tekst (debug)", value=False)

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
ui_ctx["C_Address"] = st.text_input("Arbejdsgiver adresse", auto.get("C_Address", ""))
ui_ctx["C_CoRegCVR"] = st.text_input("CVR", auto.get("C_CoRegCVR",""))
ui_ctx["P_Name"] = st.text_input("Medarbejder", auto.get("P_Name",""))
ui_ctx["P_Address"] = st.text_input("Medarbejder adresse", auto.get("P_Address", ""))
ui_ctx["MonthlySalary"] = st.text_input("Månedsløn (DKK)", auto.get("MonthlySalary",""))
ui_ctx["EmploymentStart"] = st.text_input("Ansættelsesstart", auto.get("EmploymentStart",""))
ui_ctx["TerminationDate"] = st.text_input("Opsigelsesdato", auto.get("TerminationDate",""))
ui_ctx["SeparationDate"] = st.text_input("Fratrædelsesdato", auto.get("SeparationDate",""))
ui_ctx["GardenLeaveStart"] = st.text_input("Fritstilling fra", auto.get("GardenLeaveStart",""))
ui_ctx["HealthInsuranceIncluded"] = st.checkbox("Behold sundhedsforsikring?", value=False)
ui_ctx["PensionIncluded"] = st.checkbox("Behold pensionsordning?", value=False)
ui_ctx["LunchSchemeIncluded"] = st.checkbox("Med i frokostordning indtil fritstilling?", value=False)
ui_ctx["AccrualMonth"] = st.text_input("Ferie Optjeningsmåned (fx september)", "")
ui_ctx["AccrualYear"] = st.text_input("Ferie Optjeningsår (fx 2025)", "")
ui_ctx["AccruedVacationDays"] = st.text_input("Optjente feriedage (antal)", "2,08")
ui_ctx["VacationFundName"] = st.text_input("Feriefond (fx FerieKonto)", "FerieKonto")
# --- Mobilkompensation ---
ui_ctx["MobileCompIncluded"] = st.checkbox("Mobilkompensation med?", value=False)
if ui_ctx["MobileCompIncluded"]:
    ui_ctx["MobileCompAmount"] = st.text_input("Mobilkompensation (kr./md.)", "275")
    ui_ctx["MobileCompStartDate"] = st.text_input("Startdato for mobilkompensation (fx 2025-03-01)", "")
else:
    # Clear values so template won't accidentally use stale data
    ui_ctx["MobileCompAmount"] = ""
    ui_ctx["MobileCompStartDate"] = ""

# --- Overtagelse af telefonnummer ---
ui_ctx["PhoneTransferIncluded"] = st.checkbox("Overtagelse af telefonnummer?", value=False)
if ui_ctx["PhoneTransferIncluded"]:
    ui_ctx["PhoneNumber"] = st.text_input("Telefonnummer (fx +45 12 34 56 78)", "")
    ui_ctx["ManagerName"] = st.text_input("Nærmeste leder (navn)", "")
else:
    ui_ctx["PhoneNumber"] = ""
    ui_ctx["ManagerName"] = ""

ui_ctx["EmploymentClauseRef"] = st.text_input("Henvisning til imaterielle rettigheder pkt. i ansættelseskontrakten", "")
ui_ctx["ConfidentialityClauseRef"] = st.text_input("Henvisning til tavshedspligt (pkt. i ansættelseskontrakten)", "")
ui_ctx["GroupName"] = st.text_input("Navn på koncernen (fx MBWS)", "")
ui_ctx["SignatureDeadline"] = st.text_input("Frist for underskrift (dato)", "")
ui_ctx["SignatureMonth"] = st.text_input("Underskriftsmåned (fx september)", "")
ui_ctx["SignatureYear"]  = st.text_input("Underskriftsår (fx 2025)", "")
ui_ctx["RepName"]  = st.text_input("Virksomhedens repræsentant (navn)", "")
ui_ctx["RepTitle"] = st.text_input("Virksomhedens repræsentant Titel (fx Partner / HR-chef)", "")
ui_ctx["BonusEligible"] = st.checkbox("Bonus-ordning (STI) gælder?", value=False)
if ui_ctx["BonusEligible"]:
    ui_ctx["BonusYear"] = st.text_input("Bonusår", auto.get("BonusYear",""))
    ui_ctx["BonusAmount"] = st.text_input("Bonusbeløb (DKK)", auto.get("BonusAmount",""))
else:
    # Clear values so the template won't use stale data when bonus is disabled
    ui_ctx["BonusYear"] = ""
    ui_ctx["BonusAmount"] = ""
ui_ctx["LTIEligible"] = st.checkbox("Aktiebaseret aflønning (LTI) gælder?", value=False)
if ui_ctx["LTIEligible"]:
    ui_ctx["LTIProgramName"] = st.text_input("Navn på LTI-program", "Employee Ownership Program")
    ui_ctx["LTIGoodLeaver"] = st.checkbox("Good leaver?", value=True)
    ui_ctx["LTISavingShareName"] = st.text_input("Navn på 'Saving Shares' (fx B-aktier)", "B-aktier")
    ui_ctx["LTIMatchingShareName"] = st.text_input("Navn på 'Matching Shares'", "Matching Shares")
else:
    # Clear values so the template doesn’t render LTI details when not selected
    ui_ctx["LTIProgramName"] = ""
    ui_ctx["LTIGoodLeaver"] = False
    ui_ctx["LTISavingShareName"] = ""
    ui_ctx["LTIMatchingShareName"] = ""

# Vælg skabelon (gælder både enkelt- og batch-generering)
template_files = sorted(glob.glob("templates/*.docx"))
if "sel_template" not in st.session_state:
    st.session_state.sel_template = template_files[0] if template_files else ""

st.session_state.sel_template = st.selectbox(
    "Vælg skabelon (.docx)",
    options=template_files if template_files else ["<Ingen skabeloner fundet>"],
    index=0 if template_files else 0,
    disabled=not template_files,
)

if st.button("Generér Fratrædelsesaftale"):
    ctx = build_context(auto, auto, ui_ctx)
    tpl = st.session_state.sel_template or "templates/Fratrædelsesaftale - DA.docx"
    if not Path(tpl).exists():
        st.error(f"Skabelon ikke fundet: {tpl}")
    else:
        doc = DocxTemplate(tpl)
        doc.render(ctx)
        bio = BytesIO(); doc.docx.save(bio); bio.seek(0)
        st.download_button(
            "Download aftale",
            bio,
            file_name=f"Fratraedelsesaftale_{safe_slug(ctx['P_Name'])}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# col1, col2 = st.columns(2)
# with col1:
#         if st.button("Hent seneste Kontakter & Journaler"):
#             contacts_list = list(paged("/Contacts"))
#             st.session_state.contacts = {c["id"]: c for c in contacts_list}
#             st.session_state.journals = list(paged("/Journals"))
#             json.dump(st.session_state.contacts, open("contacts.json","w"), ensure_ascii=False, indent=2)
#             json.dump(st.session_state.journals, open("journals.json","w"), ensure_ascii=False, indent=2)
#             st.success(f"Hentede {len(st.session_state.contacts)} kontakter og {len(st.session_state.journals)} journaler.")

# contacts = st.session_state.contacts
# journals = st.session_state.journals
# if not contacts or not journals:
#     st.info("Tryk på 'Hent seneste Kontakter & Journaler' først.")
# st.write(f"Indlæst {len(contacts)} kontakter, {len(journals)} journaler.")

# query = st.text_input("Søg i journaler (navn/nummer):")
# view = [j for j in journals if (query.lower() in (j.get('name') or '').lower()) or (query.lower() in (j.get('number') or '').lower())]
# sel = st.multiselect("Vælg journaler", options=[f"{j.get('number')} — {j.get('name')}" for j in view])

# OUT = Path("contracts"); OUT.mkdir(exist_ok=True)

# def generate_for(j, template_path: str):
#     c = contacts.get(j.get("clientId"))
#     if not c:
#         return None, None, "Ingen klient"
#     if not template_path or not Path(template_path).exists():
#         return None, None, "Skabelon ikke fundet"

#     ctx = {"client": c, "journal": j}

#     # Gem til disk
#     doc = DocxTemplate(template_path)
#     doc.render(ctx)
#     base = f"{safe_slug(j.get('number') or 'IngenNummer')}_{safe_slug(c.get('name') or 'UkendtKlient')}"
#     filename = OUT / f"{base}.docx"
#     doc.save(filename)

#     # Kopi i hukommelsen til download
#     bio = BytesIO()
#     doc2 = DocxTemplate(template_path)
#     doc2.render(ctx)
#     doc2.docx.save(bio)
#     bio.seek(0)

#     return filename.name, bio, None


# colA, colB = st.columns(2)
# with colA:
#     if st.button("Generér for valgte"):
#         if not has_api_key():
#             st.error("Manglende API-nøgle. Angiv `LEGIS_API_KEY` i Secrets (⚙️ → Secrets) eller som miljøvariabel.")
#         elif not glob.glob("templates/*.docx"):
#             st.error("Ingen skabeloner fundet i templates/-mappen.")
#         else:
#             sel_template = st.session_state.sel_template
#             count = 0
#             generated = []
#             by_num = {j.get('number'): j for j in journals}
#             for label in sel:
#                 num = label.split(" — ", 1)[0]
#                 j = by_num.get(num)
#                 if not j:
#                     continue
#                 try:
#                     fname, buf, err = generate_for(j, sel_template)
#                     if err:
#                         st.error(f"{num}: {err}")
#                     else:
#                         generated.append((num, fname, buf))
#                         count += 1
#                 except Exception as e:
#                     st.error(f"{num}: {e}")
#             st.success(f"Genereret {count} fil(er) i contracts/")´
#             for num, fname, buf in generated:
#                 st.download_button(
#                     label=f"Hent {fname}",
#                     data=buf,
#                     file_name=fname,
#                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#                 )

# with colB:
#     if st.button("Generér ALLE journaler"):
#         if not has_api_key():
#             st.error("Manglende API-nøgle. Angiv `LEGIS_API_KEY` i Secrets (⚙️ → Secrets) eller som miljøvariabel.")
#         elif not glob.glob("templates/*.docx"):
#             st.error("Ingen skabeloner fundet i templates/-mappen.")
#         else:
#             sel_template = st.session_state.sel_template
#             count = 0
#             generated = []
#             for j in journals:
#                 try:
#                     fname, buf, err = generate_for(j, sel_template)
#                     if err:
#                         st.error(f"{j.get('number')}: {err}")
#                     else:
#                         generated.append((j.get('number'), fname, buf))
#                         count += 1
#                 except Exception as e:
#                     st.error(f"{j.get('number')}: {e}")
#             st.success(f"Genereret {count} fil(er) i contracts/")
#             for num, fname, buf in generated[:10]:
#                 st.download_button(
#                     label=f"Hent {fname}",
#                     data=buf,
#                     file_name=fname,
#                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#                 )
#             if len(generated) > 10:
#                 st.info(f"Viser de første 10 downloads her. Alle filer er gemt i: {OUT.resolve()}")