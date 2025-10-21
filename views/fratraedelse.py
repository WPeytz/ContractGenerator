from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

import streamlit as st

from core.extractors import extract_from_contract, extract_from_payslip
from core.rendering import build_fratradelse_context, render_docx, render_markdown_to_docx
from core.utils import safe_slug

DEFAULT_TEMPLATE = Path("templates/fratraedelse.md")
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

    st.write("**Virksomhedsoplysninger**")
    ui["C_Name"] = st.text_input("Arbejdsgiver", defaults.get("C_Name", ""))
    ui["C_Address"] = st.text_input("Arbejdsgiver adresse", defaults.get("C_Address", ""))
    ui["C_CoRegCVR"] = st.text_input("CVR", defaults.get("C_CoRegCVR", ""))
    ui["C_Representative"] = st.text_input("Virksomhedsrepræsentant (navn til underskrift)", "")

    st.write("**Medarbejderoplysninger**")
    ui["P_Name"] = st.text_input("Medarbejder", defaults.get("P_Name", ""))
    ui["P_Address"] = st.text_input("Medarbejder adresse", defaults.get("P_Address", ""))
    ui["MonthlySalary"] = st.text_input("Månedsløn (DKK)", defaults.get("MonthlySalary", ""))

    st.write("**Datoer**")
    ui["EmploymentStart"] = st.text_input("Ansættelsesstart", defaults.get("EmploymentStart", ""))
    ui["ContractSignedDate"] = st.text_input("Kontraktunderskrivelsesdato", "")
    ui["TerminationDate"] = st.text_input("Opsigelsesdato", defaults.get("TerminationDate", ""))
    ui["SeparationDate"] = st.text_input("Fratrædelsesdato", defaults.get("SeparationDate", ""))
    ui["ReleaseDate"] = st.text_input("Fritstillingsdato", "")
    ui["AcceptanceDeadline"] = st.text_input("Acceptfrist (fx 15. januar 2025)", "")

    st.write("**Ferie**")
    ui["HolidayLeave"] = st.checkbox("Ferie afvikles automatisk i fritstillingsperiode?", value=False)
    if not ui["HolidayLeave"]:
        ui["NoHolidayDays"] = st.text_input("Antal feriedage der ikke kan afvikles", "")
    else:
        ui["NoHolidayDays"] = ""

    st.write("**Løn og fordele**")
    ui["noOffset"] = st.checkbox("Ingen modregning af løn fra anden ansættelse?", value=False)
    ui["HealthInsuranceIncluded"] = st.checkbox("Behold sundhedsforsikring?", value=False)
    ui["PensionIncluded"] = st.checkbox("Behold pensionsordning?", value=False)
    if ui["PensionIncluded"]:
        ui["PensionPercentage"] = st.text_input("Pensionsprocent", "")
        ui["PensionAmount"] = st.text_input("Pensionsbeløb (DKK)", "")
    else:
        ui["PensionPercentage"] = ""
        ui["PensionAmount"] = ""

    ui["LunchSchemeIncluded"] = st.checkbox("Med i frokostordning indtil fritstilling?", value=False)

    st.write("**Mobiltelefon**")
    ui["MobileCompIncluded"] = st.checkbox("Mobiltelefon med?", value=False)
    if ui["MobileCompIncluded"]:
        ui["PhoneComp"] = st.checkbox("Kompensation for aflevering af mobiltelefon?", value=False)
        ui["PhoneNumber"] = st.text_input("Telefonnummer der kan overtages", "")
        ui["ManagerName"] = st.text_input("Nærmeste leder (navn)", "")
    else:
        ui["PhoneComp"] = False
        ui["PhoneNumber"] = ""
        ui["ManagerName"] = ""

    st.write("**Anciennitet og funktionærlovens § 2a**")
    ui["years_12"] = st.checkbox("12+ års anciennitet?", value=False)
    ui["years_17"] = st.checkbox("17+ års anciennitet?", value=False)

    st.write("**Aftalt fratrædelsesgodtgørelse**")
    ui["NoCompensationMonths"] = st.text_input("Antal måneder godtgørelse", "")
    ui["PensionCompensationAmount"] = st.text_input("Godtgørelse inkl. pension (DKK)", "")
    ui["fixedCompensationAmount"] = st.checkbox("Brug fast beløb i stedet?", value=False)
    if ui["fixedCompensationAmount"]:
        ui["fixedCompensationNumber"] = st.text_input("Fast godtgørelsesbeløb (DKK)", "")
    else:
        ui["fixedCompensationNumber"] = ""

    st.write("**Bonus (STI)**")
    bonus_type = st.radio("Bonustype", ["Ingen bonus", "Bonus1 - Programbaseret", "Bonus2 - Fast aftalt beløb"])
    ui["Bonus1"] = bonus_type == "Bonus1 - Programbaseret"
    ui["Bonus2"] = bonus_type == "Bonus2 - Fast aftalt beløb"

    if ui["Bonus1"]:
        ui["CashBonusProgram"] = st.text_input("Navn på bonusprogram", "")
        ui["BonusYear1"] = st.text_input("Bonus år 1", defaults.get("BonusYear", ""))
        ui["BonusYear2"] = st.text_input("Bonus år 2 (valgfri)", "")
        ui["BonusAmount1"] = ""
        ui["BonusAmount2"] = ""
    elif ui["Bonus2"]:
        ui["BonusYear1"] = st.text_input("Bonus år 1", defaults.get("BonusYear", ""))
        ui["BonusAmount1"] = st.text_input("Fast bonusbeløb år 1 (DKK)", "")
        ui["BonusYear2"] = st.text_input("Bonus år 2 (valgfri)", "")
        ui["BonusAmount2"] = st.text_input("Fast bonusbeløb år 2 (DKK, valgfri)", "")
        ui["CashBonusProgram"] = ""
    else:
        ui["CashBonusProgram"] = ""
        ui["BonusYear1"] = ""
        ui["BonusAmount1"] = ""
        ui["BonusYear2"] = ""
        ui["BonusAmount2"] = ""

    st.write("**Aktiebaseret aflønning (LTI)**")
    ui["LTIEligible"] = st.checkbox("Aktiebaseret aflønning (LTI) gælder?", value=False)
    if ui["LTIEligible"]:
        ui["LTIRights"] = st.checkbox("LTI rettigheder bevares?", value=False)
    else:
        ui["LTIRights"] = False

    st.write("**Juridisk bistand og andre forhold**")
    ui["noAssistance"] = st.checkbox("Medarbejderen er kun opfordret til (ikke bistået af) juridisk rådgiver?", value=False)
    if not ui["noAssistance"]:
        ui["EmployeeLawyer"] = st.text_input("Medarbejderens juridiske rådgiver (navn/organisation)", "")
    else:
        ui["EmployeeLawyer"] = ""

    st.write("**Lovvalg og værneting**")
    ui["Court"] = st.checkbox("Værnetingsaftale (domstol) gælder?", value=False)
    if ui["Court"]:
        ui["CityCourt"] = st.text_input("Byrets navn (fx Retten i København)", "")
    else:
        ui["CityCourt"] = ""

    ui["Tax"] = st.checkbox("Skatteforhold (§ 7 U) skal medtages?", value=False)

    # Support both .docx and .md templates
    docx_templates = sorted(Path("templates").glob("*.docx"))
    md_templates = sorted(Path("templates").glob("*.md"))
    templates = docx_templates + md_templates
    template_paths = [str(path) for path in templates]

    if STATE_KEY_TEMPLATE not in st.session_state:
        st.session_state[STATE_KEY_TEMPLATE] = template_paths[0] if template_paths else ""

    selected_template = st.selectbox(
        "Vælg skabelon (.docx eller .md)",
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

        # Determine output format based on template extension
        if template_path.suffix == ".md":
            buffer = render_markdown_to_docx(template_path, context)
            filename = f"Fratraedelsesaftale_{safe_slug(context.get('P_Name'))}.docx"
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:  # .docx
            buffer = render_docx(template_path, context)
            filename = f"Fratraedelsesaftale_{safe_slug(context.get('P_Name'))}.docx"
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        st.download_button(
            "Download aftale",
            buffer,
            file_name=filename,
            mime=mime_type,
        )
