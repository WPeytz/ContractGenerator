from typing import Callable, Dict, Optional

import pdfplumber
import re

from .utils import normalize_whitespace, parse_dk_amount, parse_dk_date

DebugCallback = Optional[Callable[[str], None]]
DK_POSTAL = r"\b[0-9]{4}\b"


def _emit_debug(callback: DebugCallback, raw_text: str) -> None:
    if callback and raw_text:
        callback(raw_text[:20000])


def extract_from_contract(pdf_path: str, debug_callback: DebugCallback = None) -> Dict[str, str]:
    """Parse employer/employee data anchored on CVR and CPR markers."""
    out: Dict[str, str] = {}
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    full_text = "\n".join(pages)

    _emit_debug(debug_callback, full_text)

    lines = [line.strip() for line in full_text.splitlines()]
    lines = [line for line in lines if line is not None]

    cvr_idx = next(
        (idx for idx, line in enumerate(lines) if re.search(r"\bCVR\b\s*:?\s*\d{8}", line, re.I)),
        None,
    )
    if cvr_idx is not None:
        match = re.search(r"\bCVR\b\s*:?\s*(\d{8})", lines[cvr_idx], re.I)
        if match:
            out["C_CoRegCVR"] = match.group(1)

        window = [line for line in lines[max(0, cvr_idx - 3):cvr_idx] if line]
        if window:
            name_line = re.sub(r"^(BETWEEN|AND)\s+", "", window[0], flags=re.I).strip()
            out["C_Name"] = name_line

            addr_parts = [w for w in window[1:] if w]
            for idx, part in enumerate(addr_parts):
                if re.search(DK_POSTAL, part):
                    addr_parts = addr_parts[: idx + 1]
                    break
            if addr_parts:
                out["C_Address"] = normalize_whitespace(" ".join(addr_parts))

    cpr_idx = next(
        (
            idx
            for idx, line in enumerate(lines)
            if re.search(r"\bCPR\b\s*:?$", line, re.I)
            or re.search(r"\bCPR\b\s*:", line, re.I)
        ),
        None,
    )
    if cpr_idx is not None:
        window = [line for line in lines[max(0, cpr_idx - 4):cpr_idx] if line]
        if window:
            name_line = None
            for item in reversed(window):
                if not re.search(r"\d", item):
                    name_line = re.sub(r"^(BETWEEN|AND)\s+", "", item, flags=re.I).strip()
                    break
            if name_line:
                out["P_Name"] = normalize_whitespace(name_line)

            postal_idx = None
            for idx, item in enumerate(window):
                if re.search(DK_POSTAL, item):
                    postal_idx = idx
                    break
            if postal_idx is not None:
                street = window[postal_idx - 1].strip() if postal_idx - 1 >= 0 else ""
                postal = window[postal_idx].strip()
                out["P_Address"] = normalize_whitespace(f"{street} {postal}".strip())
            else:
                addr_candidates = [item for item in window if re.search(r"\d", item)]
                if addr_candidates:
                    out["P_Address"] = normalize_whitespace(addr_candidates[-1])
    else:
        match = re.search(r"\bAND\b\s*(.+)$", full_text, re.I | re.M)
        if match:
            tail = [segment.strip() for segment in match.group(1).splitlines() if segment.strip()]
            if tail:
                out.setdefault("P_Name", tail[0])
            for segment in tail[1:4]:
                if re.search(DK_POSTAL, segment):
                    out.setdefault("P_Address", normalize_whitespace(segment))
                    break

    effective_match = re.search(
        r"With effect from ([A-Za-z0-9,\.\-\/\s]+?),\s*the Employee is employed",
        full_text,
        re.I,
    )
    if effective_match:
        out["EmploymentStart"] = parse_dk_date(effective_match.group(1))

    patterns = [
        r"fixed\s+annual\s+salary\s+of\s+(?:DKK|kr\.?)[\s]*([\d\.,]+)",
        r"(?:gross\s+)?monthly\s+salary\s+(?:is|of)\s+(?:DKK|kr\.?)[\s]*([\d\.,]+)",
        r"(?:base|fixed)?\s*salary\s*(?:is|of|amounts\s*to)\s*(?:DKK|kr\.?)?\s*([\d\.,]+)\s*(?:per\s*month|pr\.\s*måned|monthly)",
        r"\bmånedsløn\b[^\d]*([\d\.,]+)",
        r"\bårsløn\b[^\d]*([\d\.,]+)",
    ]
    monthly = None
    for pattern in patterns:
        match = re.search(pattern, full_text, re.I)
        if not match:
            continue
        amount = parse_dk_amount(match.group(1))
        try:
            if "årsløn" in pattern or "annual" in pattern:
                monthly = float(amount) / 12.0
            else:
                monthly = float(amount)
            break
        except Exception:
            pass

    if monthly is not None and monthly > 5000:
        out["MonthlySalary"] = f"{monthly:.2f}".rstrip("0").rstrip(".")

    bonus_year_match = re.search(r"\bbonus(?:året|year)?\s*(?:for\s*)?(20\d{2})\b", full_text, re.I)
    if bonus_year_match:
        out["BonusYear"] = bonus_year_match.group(1)

    bonus_amount_match = re.search(r"bonus\s*(?:på|of)?\s*(?:DKK|kr\.?)?\s*([\d\.\,]+)", full_text, re.I)
    if bonus_amount_match:
        value = parse_dk_amount(bonus_amount_match.group(1))
        if value:
            out["BonusAmount"] = value

    def _find_clause_number(text: str, keywords) -> Optional[str]:
        pattern_primary = re.compile(
            r"^(?:\s*(?:Section|Pkt\.?|Punkt)\s*)?(\d{1,2}(?:\.\d+)*)\s*[-–.)]?\s*(%s)\b"
            % "|".join(keywords),
            re.I | re.M,
        )
        match_primary = pattern_primary.search(text)
        if match_primary:
            return match_primary.group(1)

        pattern_inline = re.compile(
            r"(?:clause|pkt\.?|punkt)\s*(\d+(?:\.\d+)*)\s*(?:om|on)?\s*(%s)"
            % "|".join(keywords),
            re.I,
        )
        match_inline = pattern_inline.search(text)
        if match_inline:
            return match_inline.group(1)

        lines_local = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for idx, line in enumerate(lines_local[:-1]):
            if re.match(r"^(?:Section\s*)?(\d{1,2}(?:\.\d+)*)\s*[-–.)]?$", line, re.I):
                next_line = lines_local[idx + 1]
                if re.search(r"\b(?:%s)\b" % "|".join(keywords), next_line, re.I):
                    num_match = re.match(r"^(?:Section\s*)?(\d{1,2}(?:\.\d+)*)", line, re.I)
                    if num_match:
                        return num_match.group(1)
        return None

    conf_keywords = ["Confidentiality", "Tavshedspligt", "Non\s*Disclosure", "Fortrolighed"]
    ip_keywords = ["Intellectual\s*Property", "Immaterielle\s*rettigheder", "IP\s*Rights", "Immaterial\s*rights"]

    if not out.get("ConfidentialityClauseRef"):
        reference = _find_clause_number(full_text, conf_keywords)
        if reference:
            out["ConfidentialityClauseRef"] = reference

    if not out.get("EmploymentClauseRef"):
        reference = _find_clause_number(full_text, ip_keywords)
        if reference:
            out["EmploymentClauseRef"] = reference

    return out


def extract_from_payslip(pdf_path: str, debug_callback: DebugCallback = None) -> Dict[str, str]:
    out: Dict[str, str] = {}
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    full_text = "\n".join(pages)
    flattened = normalize_whitespace(full_text)

    _emit_debug(debug_callback, full_text)

    match = re.search(r"\bFra:\s*([0-9\-\.\/]+).*?\bTil:\s*([0-9\-\.\/]+)", full_text, re.I | re.S)
    if match:
        out["PeriodFrom"] = parse_dk_date(match.group(1))
        out["PeriodTo"] = parse_dk_date(match.group(2))

    labels = [
        r"Fast\s*månedsløn",
        r"Brutto\s*månedsløn",
        r"Månedsløn",
        r"Fast\s*løn",
        r"Løn\s*\(måned\)",
    ]

    lines = [line for line in full_text.splitlines() if line.strip()]
    found_label_amount = False
    for label in labels:
        pattern = re.compile(label, re.I)
        for idx, line in enumerate(lines):
            if not pattern.search(line):
                continue
            combined = line + (" " + lines[idx + 1] if idx + 1 < len(lines) else "")
            numbers = re.findall(r"[\d\.,]+", combined)
            candidates = []
            for raw in numbers:
                value = parse_dk_amount(raw)
                try:
                    number = float(value)
                except Exception:
                    continue
                if 5000 < number < 300000:
                    candidates.append(number)
            if candidates:
                best = max(candidates)
                out["MonthlySalary"] = f"{best:.2f}".rstrip("0").rstrip(".")
                found_label_amount = True
                break
        if found_label_amount:
            break

    if "MonthlySalary" not in out:
        salary_candidates = []
        for match in re.finditer(r"(?i)l[øo]n[^\n\r]{0,80}?([\d\.,]+)", full_text):
            segment = full_text[max(0, match.start() - 20): match.end() + 20]
            if re.search(r"netto\s*l[øo]n|nettol[øo]n|netto", segment, re.I):
                continue
            if re.search(r"AM\s*-\s*bidrag|AM-bidrag|A\s*-\s*skat|A-skat", segment, re.I):
                continue
            value = parse_dk_amount(match.group(1))
            try:
                number = float(value)
                if 5000 < number < 300000:
                    salary_candidates.append(number)
            except Exception:
                pass
        if salary_candidates:
            best = max(salary_candidates)
            out["MonthlySalary"] = f"{best:.2f}".rstrip("0").rstrip(".")

    name_match = re.search(r"\bNavn\b\s*:\s*([^\n\r]+)", full_text, re.I)
    if name_match:
        out["P_Name"] = normalize_whitespace(name_match.group(1))

    bonus_candidates = []
    for match in re.finditer(r"bonus[^\n\r]*?([\d\.,]+)", full_text, re.I):
        value = parse_dk_amount(match.group(1))
        try:
            number = float(value)
            if number > 0:
                bonus_candidates.append(number)
        except Exception:
            pass
    if bonus_candidates:
        best = max(bonus_candidates)
        out["BonusAmount"] = f"{best:.2f}".rstrip("0").rstrip(".")

    year_match = re.search(r"\bbonus(?:året|year)?\s*(?:for\s*)?(20\d{2})\b", full_text, re.I)
    if not year_match:
        tail = out.get("PeriodTo") or out.get("PeriodFrom")
        if tail and re.match(r"\d{4}-\d{2}-\d{2}", tail):
            year_match = re.match(r"(\d{4})", tail)
    if year_match:
        out["BonusYear"] = year_match.group(1) if hasattr(year_match, "group") else year_match

    return out
