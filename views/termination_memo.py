from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

import streamlit as st

from core.extractors import extract_from_contract
from core.rendering import render_docx
from core.utils import safe_slug, format_date_long

DEFAULT_TEMPLATE = Path("templates/Updated Memo - Termination.docx")
STATE_KEY_TEMPLATE = "termination_memo_selected_template"


def _write_temp_file(uploaded_file) -> str:
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


def render() -> None:
    st.header("Termination Memo")

    contract_file = st.file_uploader(
        "Upload ansættelseskontrakt (PDF) for automatisk udfyldning (valgfrit)",
        type=["pdf"],
        key="termination_contract_file",
    )

    contract_data: Dict[str, str] = {}
    if contract_file is not None:
        tmp_path = _write_temp_file(contract_file)
        contract_data.update(extract_from_contract(tmp_path))

    st.subheader("Memo oplysninger")
    col_left, col_right = st.columns(2)
    with col_left:
        p_name = st.text_input("Medarbejder navn", contract_data.get("P_Name", ""))
        p_title = st.text_input("Medarbejder titel", "")
        c_name = st.text_input("Virksomhed", contract_data.get("C_Name", ""))
        start_date = st.text_input("Startdato", contract_data.get("EmploymentStart", ""))
        today_date = st.text_input("Dags dato", "")
        signed_date = st.text_input("Dato for underskrift", "")
        acceptence_date = st.text_input("Dato for accept", "")
        negotiation_date = st.text_input("Forhandlingsdato", "")
    with col_right:
        sick_date = st.text_input("Sygemeldingsdato", "")
        no_sick_months = st.text_input("Antal måneder sygemeldt", "")
        at_risk_date = st.text_input("Dato for varsling (at risk)", "")
        chosen_communication_date = st.text_input("Dato for kommunikation valgt", "")
        clarification_period_date = st.text_input("Dato for afklaringsperiode", "")
        deadline_expires_date = st.text_input("Frist udløber dato", "")
        internal_review_date = st.text_input("Intern review dato", "")
        preliminary_decision_date = st.text_input("Foreløbig beslutning dato", "")

    context = {
        "P_Name": p_name,
        "P_Title": p_title,
        "C_Name": c_name,
        "Start_Date": format_date_long(start_date),
        "Today_Date": today_date,
        "Signed_Date": signed_date,
        "Acceptence_Date": acceptence_date,
        "Negotiation_Date": negotiation_date,
        "Sick_Date": sick_date,
        "No_Sick_Months": no_sick_months,
        "At_Risk_date": at_risk_date,
        "Chosen_Communication_Date": chosen_communication_date,
        "Clarification_Period_Date": clarification_period_date,
        "Deadline_Expires_Date": deadline_expires_date,
        "Internal_Review_Date": internal_review_date,
        "Preliminary_Decision_Date": preliminary_decision_date,
    }

    templates = sorted(Path("templates").glob("*.docx"))
    template_paths = [str(path) for path in templates]

    if STATE_KEY_TEMPLATE not in st.session_state:
        st.session_state[STATE_KEY_TEMPLATE] = template_paths[0] if template_paths else ""

    selected_template = st.selectbox(
        "Vælg memo skabelon (.docx)",
        options=template_paths if template_paths else [""],
        index=0 if template_paths else 0,
        format_func=lambda path: Path(path).name if path else "<Ingen skabeloner fundet>",
        disabled=not template_paths,
        key=STATE_KEY_TEMPLATE,
    )

    if st.button("Generér termination memo"):
        template_path = Path(selected_template or DEFAULT_TEMPLATE)
        if not template_path.exists():
            st.error(f"Skabelon ikke fundet: {template_path}")
            return
        buffer = render_docx(template_path, context)
        filename = f"TerminationMemo_{safe_slug(context.get('P_Name'))}.docx"
        st.download_button(
            "Download memo",
            buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
