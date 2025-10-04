from io import BytesIO
from pathlib import Path
from typing import Dict, Mapping

from docxtpl import DocxTemplate

from .utils import format_currency, parse_dk_amount


def build_fratradelse_context(
    contract_data: Mapping[str, str],
    payslip_data: Mapping[str, str],
    ui_data: Mapping[str, str],
) -> Dict[str, str]:
    salary = (
        payslip_data.get("MonthlySalary")
        or contract_data.get("MonthlySalary")
        or ui_data.get("MonthlySalary")
    )
    normalized_salary = parse_dk_amount(salary) or salary

    bonus_enabled = ui_data.get("BonusEligible")
    bonus_year = ui_data.get("BonusYear") if bonus_enabled else ""
    bonus_amount_raw = ui_data.get("BonusAmount") if bonus_enabled else ""
    bonus_amount_normalized = parse_dk_amount(bonus_amount_raw) if bonus_amount_raw else ""
    bonus_amount_formatted = format_currency(bonus_amount_normalized) if bonus_amount_normalized else ""

    return {
        "C_Name": contract_data.get("C_Name") or ui_data.get("C_Name"),
        "C_Address": ui_data.get("C_Address", ""),
        "C_CoRegCVR": contract_data.get("C_CoRegCVR") or ui_data.get("C_CoRegCVR"),
        "P_Name": contract_data.get("P_Name") or ui_data.get("P_Name"),
        "P_Address": ui_data.get("P_Address", ""),
        "MonthlySalary": format_currency(normalized_salary) if normalized_salary else "",
        "BonusYear": bonus_year,
        "BonusAmount": bonus_amount_raw,
        "BonusAmountFmt": bonus_amount_formatted,
        "LTIEligible": ui_data.get("LTIEligible"),
        "LTIProgramName": ui_data.get("LTIProgramName"),
        "LTIGoodLeaver": ui_data.get("LTIGoodLeaver"),
        "LTISavingShareName": ui_data.get("LTISavingShareName"),
        "LTIMatchingShareName": ui_data.get("LTIMatchingShareName"),
        "EmploymentStart": contract_data.get("EmploymentStart") or ui_data.get("EmploymentStart"),
        "TerminationDate": ui_data.get("TerminationDate"),
        "SeparationDate": ui_data.get("SeparationDate"),
        "GardenLeaveStart": ui_data.get("GardenLeaveStart"),
        "AccrualMonth": ui_data.get("AccrualMonth"),
        "AccrualYear": ui_data.get("AccrualYear"),
        "HealthInsuranceIncluded": ui_data.get("HealthInsuranceIncluded"),
        "PensionIncluded": ui_data.get("PensionIncluded"),
        "LunchSchemeIncluded": ui_data.get("LunchSchemeIncluded"),
        "PhoneTransferIncluded": ui_data.get("PhoneTransferIncluded"),
        "PhoneNumber": ui_data.get("PhoneNumber"),
        "ManagerName": ui_data.get("ManagerName"),
        "EmploymentClauseRef": contract_data.get("EmploymentClauseRef") or ui_data.get("EmploymentClauseRef"),
        "ConfidentialityClauseRef": contract_data.get("ConfidentialityClauseRef") or ui_data.get("ConfidentialityClauseRef"),
        "GroupName": ui_data.get("GroupName"),
        "SignatureDeadline": ui_data.get("SignatureDeadline"),
        "SignatureMonth": ui_data.get("SignatureMonth"),
        "SignatureYear": ui_data.get("SignatureYear"),
        "RepName": ui_data.get("RepName"),
        "RepTitle": ui_data.get("RepTitle"),
        "AccruedVacationDays": ui_data.get("AccruedVacationDays"),
        "VacationFundName": ui_data.get("VacationFundName"),
        "BonusEligible": ui_data.get("BonusEligible"),
        "MobileCompIncluded": ui_data.get("MobileCompIncluded"),
        "MobileCompAmount": ui_data.get("MobileCompAmount"),
        "MobileCompStartDate": ui_data.get("MobileCompStartDate"),
    }


def render_docx(template_path: Path, context: Mapping[str, str]) -> BytesIO:
    template = DocxTemplate(str(template_path))
    template.render(context)
    buffer = BytesIO()
    template.docx.save(buffer)
    buffer.seek(0)
    return buffer
