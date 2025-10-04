from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

import streamlit as st

from core.extractors import extract_from_contract, extract_from_payslip
from core.rendering import build_fratradelse_context, render_docx
from core.utils import safe_slug

DEFAULT_TEMPLATE = Path("templates/Fratrædelsesaftale - DA.docx")
STATE_KEY_TEMPLATE = "fratraedelse_selected_template"


def _write_temp_file(uploaded_file) -> str:
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


def render() -> None:
    st.header("Auto-udfyld Fratrædelsesaftale")

    show_debug = st.checkbox("Vis rå PDF-tekst (debug)", value=False)
    contract_debug_cb = None
    payslip_debug_cb = None
    if show_debug:
        contract_expander = st.expander("Kontrakt: rå tekst")
        payslip_expander = st.expander("Lønseddel: rå tekst")
        contract_debug_cb = lambda text: contract_expander.text(text)
        payslip_debug_cb = lambda text: payslip_expander.text(text)

    col_contract, col_payslip = st.columns(2)
    with col_contract:
        contract_file = st.file_uploader(
            "Upload ansættelseskontrakt (PDF)",
            type=["pdf"],
            key="contract_file",
        )
    with col_payslip:
        payslip_file = st.file_uploader(
            "Upload lønseddel (PDF)",
            type=["pdf"],
            key="payslip_file",
        )

    contract_data: Dict[str, str] = {}
    payslip_data: Dict[str, str] = {}

    if contract_file is not None:
        tmp_path = _write_temp_file(contract_file)
        contract_data.update(extract_from_contract(tmp_path, debug_callback=contract_debug_cb))

    if payslip_file is not None:
        tmp_path = _write_temp_file(payslip_file)
        payslip_data.update(extract_from_payslip(tmp_path, debug_callback=payslip_debug_cb))

    defaults = {**contract_data, **payslip_data}

    st.subheader("Ret/tilføj oplysninger")
    ui = {}
    ui["C_Name"] = st.text_input("Arbejdsgiver", defaults.get("C_Name", ""))
    ui["C_Address"] = st.text_input("Arbejdsgiver adresse", defaults.get("C_Address", ""))
    ui["C_CoRegCVR"] = st.text_input("CVR", defaults.get("C_CoRegCVR", ""))
    ui["P_Name"] = st.text_input("Medarbejder", defaults.get("P_Name", ""))
    ui["P_Address"] = st.text_input("Medarbejder adresse", defaults.get("P_Address", ""))
    ui["MonthlySalary"] = st.text_input("Månedsløn (DKK)", defaults.get("MonthlySalary", ""))
    ui["EmploymentStart"] = st.text_input("Ansættelsesstart", defaults.get("EmploymentStart", ""))
    ui["TerminationDate"] = st.text_input("Opsigelsesdato", defaults.get("TerminationDate", ""))
    ui["SeparationDate"] = st.text_input("Fratrædelsesdato", defaults.get("SeparationDate", ""))
    ui["GardenLeaveStart"] = st.text_input("Fritstilling fra", defaults.get("GardenLeaveStart", ""))
    ui["HealthInsuranceIncluded"] = st.checkbox("Behold sundhedsforsikring?", value=False)
    ui["PensionIncluded"] = st.checkbox("Behold pensionsordning?", value=False)
    ui["LunchSchemeIncluded"] = st.checkbox("Med i frokostordning indtil fritstilling?", value=False)
    ui["AccrualMonth"] = st.text_input("Ferie Optjeningsmåned (fx september)", "")
    ui["AccrualYear"] = st.text_input("Ferie Optjeningsår (fx 2025)", "")
    ui["AccruedVacationDays"] = st.text_input("Optjente feriedage (antal)", "2,08")
    ui["VacationFundName"] = st.text_input("Feriefond (fx FerieKonto)", "FerieKonto")

    ui["MobileCompIncluded"] = st.checkbox("Mobilkompensation med?", value=False)
    if ui["MobileCompIncluded"]:
        ui["MobileCompAmount"] = st.text_input("Mobilkompensation (kr./md.)", "275")
        ui["MobileCompStartDate"] = st.text_input(
            "Startdato for mobilkompensation (fx 2025-03-01)",
            "",
        )
    else:
        ui["MobileCompAmount"] = ""
        ui["MobileCompStartDate"] = ""

    ui["PhoneTransferIncluded"] = st.checkbox("Overtagelse af telefonnummer?", value=False)
    if ui["PhoneTransferIncluded"]:
        ui["PhoneNumber"] = st.text_input("Telefonnummer (fx +45 12 34 56 78)", "")
        ui["ManagerName"] = st.text_input("Nærmeste leder (navn)", "")
    else:
        ui["PhoneNumber"] = ""
        ui["ManagerName"] = ""

    ui["EmploymentClauseRef"] = st.text_input(
        "Henvisning til imaterielle rettigheder pkt. i ansættelseskontrakten",
        "",
    )
    ui["ConfidentialityClauseRef"] = st.text_input(
        "Henvisning til tavshedspligt (pkt. i ansættelseskontrakten)",
        "",
    )
    ui["GroupName"] = st.text_input("Navn på koncernen (fx MBWS)", "")
    ui["SignatureDeadline"] = st.text_input("Frist for underskrift (dato)", "")
    ui["SignatureMonth"] = st.text_input("Underskriftsmåned (fx september)", "")
    ui["SignatureYear"] = st.text_input("Underskriftsår (fx 2025)", "")
    ui["RepName"] = st.text_input("Virksomhedens repræsentant (navn)", "")
    ui["RepTitle"] = st.text_input(
        "Virksomhedens repræsentant Titel (fx Partner / HR-chef)",
        "",
    )

    ui["BonusEligible"] = st.checkbox("Bonus-ordning (STI) gælder?", value=False)
    if ui["BonusEligible"]:
        ui["BonusYear"] = st.text_input("Bonusår", defaults.get("BonusYear", ""))
        ui["BonusAmount"] = st.text_input("Bonusbeløb (DKK)", defaults.get("BonusAmount", ""))
    else:
        ui["BonusYear"] = ""
        ui["BonusAmount"] = ""

    ui["LTIEligible"] = st.checkbox("Aktiebaseret aflønning (LTI) gælder?", value=False)
    if ui["LTIEligible"]:
        ui["LTIProgramName"] = st.text_input("Navn på LTI-program", "Employee Ownership Program")
        ui["LTIGoodLeaver"] = st.checkbox("Good leaver?", value=True)
        ui["LTISavingShareName"] = st.text_input("Navn på 'Saving Shares' (fx B-aktier)", "B-aktier")
        ui["LTIMatchingShareName"] = st.text_input("Navn på 'Matching Shares'", "Matching Shares")
    else:
        ui["LTIProgramName"] = ""
        ui["LTIGoodLeaver"] = False
        ui["LTISavingShareName"] = ""
        ui["LTIMatchingShareName"] = ""

    templates = sorted(Path("templates").glob("*.docx"))
    template_paths = [str(path) for path in templates]

    if STATE_KEY_TEMPLATE not in st.session_state:
        st.session_state[STATE_KEY_TEMPLATE] = template_paths[0] if template_paths else ""

    selected_template = st.selectbox(
        "Vælg skabelon (.docx)",
        options=template_paths if template_paths else [""],
        index=0 if template_paths else 0,
        format_func=lambda path: Path(path).name if path else "<Ingen skabeloner fundet>",
        disabled=not template_paths,
        key=STATE_KEY_TEMPLATE,
    )

    if st.button("Generér Fratrædelsesaftale"):
        template_path = Path(selected_template or DEFAULT_TEMPLATE)
        if not template_path.exists():
            st.error(f"Skabelon ikke fundet: {template_path}")
            return

        context = build_fratradelse_context(contract_data, payslip_data, ui)
        buffer = render_docx(template_path, context)
        filename = f"Fratraedelsesaftale_{safe_slug(context.get('P_Name'))}.docx"
        st.download_button(
            "Download aftale",
            buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
