from io import BytesIO
from pathlib import Path
from typing import Dict, Mapping
import tempfile
import os

from docxtpl import DocxTemplate
from jinja2 import Template
import markdown

from .utils import format_currency, parse_dk_amount, format_date_long

# Import WeasyPrint only when needed (for PDF rendering)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False
    HTML = None


def build_fratradelse_context(
    contract_data: Mapping[str, str],
    payslip_data: Mapping[str, str],
    ui_data: Mapping[str, str],
) -> Dict[str, str]:
    """Build context dictionary for fratradelse template rendering."""
    salary = (
        payslip_data.get("MonthlySalary")
        or contract_data.get("MonthlySalary")
        or ui_data.get("MonthlySalary")
    )
    normalized_salary = parse_dk_amount(salary) or salary

    # Handle Bonus1
    bonus1_enabled = ui_data.get("Bonus1")
    bonus1_year = ui_data.get("BonusYear1") if bonus1_enabled else ""
    bonus1_amount_raw = ui_data.get("BonusAmount1") if bonus1_enabled else ""
    bonus1_amount_normalized = parse_dk_amount(bonus1_amount_raw) if bonus1_amount_raw else ""
    bonus1_amount_formatted = format_currency(bonus1_amount_normalized) if bonus1_amount_normalized else ""

    # Handle Bonus2 (optional second bonus within Bonus1 section)
    bonus2_year = ui_data.get("BonusYear2") if bonus1_enabled else ""
    bonus2_amount_raw = ui_data.get("BonusAmount2") if bonus1_enabled else ""
    bonus2_amount_normalized = parse_dk_amount(bonus2_amount_raw) if bonus2_amount_raw else ""
    bonus2_amount_formatted = format_currency(bonus2_amount_normalized) if bonus2_amount_normalized else ""

    # Handle pension amounts
    pension_amount_raw = ui_data.get("PensionAmount")
    pension_amount_normalized = parse_dk_amount(pension_amount_raw) if pension_amount_raw else ""
    pension_amount_formatted = format_currency(pension_amount_normalized) if pension_amount_normalized else ""

    # Handle compensation amounts
    comp_amount_raw = ui_data.get("CompensationAmount")
    comp_amount_normalized = parse_dk_amount(comp_amount_raw) if comp_amount_raw else ""
    comp_amount_formatted = format_currency(comp_amount_normalized) if comp_amount_normalized else ""

    pension_comp_amount_raw = ui_data.get("PensionCompensationAmount", "")
    pension_comp_normalized = parse_dk_amount(pension_comp_amount_raw) if pension_comp_amount_raw else ""
    pension_comp_formatted = format_currency(pension_comp_normalized) if pension_comp_normalized else ""

    fixed_comp_raw = ui_data.get("fixedCompensationNumber", "")
    fixed_comp_normalized = parse_dk_amount(fixed_comp_raw) if fixed_comp_raw else ""
    fixed_comp_formatted = format_currency(fixed_comp_normalized) if fixed_comp_normalized else ""

    return {
        # Company info
        "C_Name": contract_data.get("C_Name") or ui_data.get("C_Name"),
        "C_Address": ui_data.get("C_Address", ""),
        "C_CoRegCVR": contract_data.get("C_CoRegCVR") or ui_data.get("C_CoRegCVR"),
        "C_Representative": ui_data.get("C_Representative", ""),
        # Person info
        "P_Name": contract_data.get("P_Name") or ui_data.get("P_Name"),
        "P_Address": ui_data.get("P_Address", ""),
        # Salary
        "MonthlySalary": format_currency(normalized_salary) if normalized_salary else "",
        # Compensation
        "CompensationAmount": comp_amount_formatted or comp_amount_raw,
        "CompensationNoMonths": ui_data.get("CompensationNoMonths"),
        "CompensationFixedAmount": ui_data.get("CompensationFixedAmount"),
        "NoCompensationMonths": ui_data.get("NoCompensationMonths"),
        "PensionCompensationAmount": pension_comp_formatted or pension_comp_raw,
        "fixedCompensationAmount": ui_data.get("fixedCompensationAmount"),
        "fixedCompensationNumber": fixed_comp_formatted or fixed_comp_raw,
        # Bonus fields
        "Bonus1": ui_data.get("Bonus1"),
        "Bonus2": ui_data.get("Bonus2"),
        "CashBonusProgram": ui_data.get("CashBonusProgram", ""),
        "BonusYear1": bonus1_year,
        "BonusAmount1": bonus1_amount_formatted or bonus1_amount_raw,
        "BonusYear2": bonus2_year,
        "BonusAmount2": bonus2_amount_formatted or bonus2_amount_raw,
        # LTI fields
        "LTIEligible": ui_data.get("LTIEligible"),
        "LTIRights": ui_data.get("LTIRights"),
        # Date fields - format all dates to Danish long form (e.g., "15. August 2022")
        "EmploymentStart": format_date_long(contract_data.get("EmploymentStart") or ui_data.get("EmploymentStart")),
        "ContractSignedDate": format_date_long(ui_data.get("ContractSignedDate")),
        "TerminationDate": format_date_long(ui_data.get("TerminationDate")),
        "SeparationDate": format_date_long(ui_data.get("SeparationDate")),
        "ReleaseDate": format_date_long(ui_data.get("ReleaseDate")),
        "AcceptanceDeadline": ui_data.get("AcceptanceDeadline", ""),
        # Holiday
        "HolidayLeave": ui_data.get("HolidayLeave"),
        "NoHolidayDays": ui_data.get("NoHolidayDays", ""),
        # Benefits
        "HealthInsuranceIncluded": ui_data.get("HealthInsuranceIncluded"),
        "PensionIncluded": ui_data.get("PensionIncluded"),
        "PensionPercentage": ui_data.get("PensionPercentage"),
        "PensionAmount": pension_amount_formatted or pension_amount_raw,
        "LunchSchemeIncluded": ui_data.get("LunchSchemeIncluded"),
        # Contact info
        "PhoneNumber": ui_data.get("PhoneNumber"),
        "ManagerName": ui_data.get("ManagerName"),
        # Mobile compensation
        "MobileCompIncluded": ui_data.get("MobileCompIncluded"),
        "PhoneComp": ui_data.get("PhoneComp"),
        "MobileCompStartDate": format_date_long(ui_data.get("MobileCompStartDate")),
        # Court and tax
        "Court": ui_data.get("Court"),
        "CityCourt": ui_data.get("CityCourt"),
        "Tax": ui_data.get("Tax"),
        "noAssistance": ui_data.get("noAssistance"),
        "EmployeeLawyer": ui_data.get("EmployeeLawyer", ""),
        "noOffset": ui_data.get("noOffset"),
        # Service years
        "years_12": ui_data.get("years_12"),
        "years_17": ui_data.get("years_17"),
    }


def render_docx(template_path: Path, context: Mapping[str, str]) -> BytesIO:
    template = DocxTemplate(str(template_path))
    template.render(context)
    buffer = BytesIO()
    template.docx.save(buffer)
    buffer.seek(0)
    return buffer


def render_markdown_to_pdf(template_path: Path, context: Mapping[str, str]) -> BytesIO:
    """Render a Markdown template with Jinja2 variables to PDF."""
    if not WEASYPRINT_AVAILABLE:
        raise ImportError(
            "WeasyPrint is not available. Please install the required system libraries. "
            "See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation"
        )

    # Read the Markdown template
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Render Jinja2 variables
    jinja_template = Template(template_content)
    rendered_markdown = jinja_template.render(context)

    # Convert Markdown to HTML
    html_content = markdown.markdown(rendered_markdown, extensions=['extra', 'nl2br'])

    # Add basic CSS styling for better PDF output with automatic section numbering
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Verdana, sans-serif;
                line-height: 1.4;
                margin: 40px;
                font-size: 9pt;
                counter-reset: section;
            }}
            h1, h2, h3 {{
                color: #000;
                font-family: Verdana, sans-serif;
            }}
            h1 {{
                font-size: 9pt;
                font-weight: bold;
                margin-top: 0;
                margin-bottom: 12pt;
            }}
            h2 {{
                font-size: 9pt;
                font-weight: bold;
                margin-top: 12pt;
                margin-bottom: 12pt;
                counter-increment: section;
            }}
            h2::before {{
                content: counter(section) " ";
            }}
            p {{
                margin: 0;
                margin-bottom: 12pt;
            }}
            hr {{
                border: none;
                border-top: 1px solid #ccc;
                margin: 20px 0;
            }}
            ul, ol {{
                margin-bottom: 12pt;
            }}
            li {{
                margin-bottom: 12pt;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    buffer = BytesIO()
    HTML(string=styled_html).write_pdf(buffer)
    buffer.seek(0)
    return buffer


def render_markdown_to_docx(template_path: Path, context: Mapping[str, str]) -> BytesIO:
    """Render a Markdown template with Jinja2 variables to Word document."""
    try:
        import pypandoc

        # Read the Markdown template
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Render Jinja2 variables
        jinja_template = Template(template_content)
        rendered_markdown = jinja_template.render(context)

        # Create a temporary file for the markdown content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(rendered_markdown)
            temp_md_path = temp_md.name

        # Create a temporary file for the docx output
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
            temp_docx_path = temp_docx.name

        try:
            # Convert markdown to docx using pypandoc
            extra_args = [
                '--number-sections',  # Enable section numbering
            ]
            if Path('templates/reference.docx').exists():
                extra_args.append('--reference-doc=templates/reference.docx')

            pypandoc.convert_file(
                temp_md_path,
                'docx',
                outputfile=temp_docx_path,
                extra_args=extra_args
            )

            # Read the generated docx into a BytesIO buffer
            with open(temp_docx_path, 'rb') as f:
                buffer = BytesIO(f.read())
            buffer.seek(0)
            return buffer

        finally:
            # Clean up temporary files
            if os.path.exists(temp_md_path):
                os.unlink(temp_md_path)
            if os.path.exists(temp_docx_path):
                os.unlink(temp_docx_path)

    except ImportError:
        # Fallback: use subprocess to call pandoc directly
        import subprocess

        # Read the Markdown template
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Render Jinja2 variables
        jinja_template = Template(template_content)
        rendered_markdown = jinja_template.render(context)

        # Create a temporary file for the markdown content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(rendered_markdown)
            temp_md_path = temp_md.name

        # Create a temporary file for the docx output
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
            temp_docx_path = temp_docx.name

        try:
            # Convert markdown to docx using pandoc command
            cmd = ['pandoc', temp_md_path, '-o', temp_docx_path, '--number-sections']
            if Path('templates/reference.docx').exists():
                cmd.extend(['--reference-doc=templates/reference.docx'])

            subprocess.run(cmd, check=True)

            # Read the generated docx into a BytesIO buffer
            with open(temp_docx_path, 'rb') as f:
                buffer = BytesIO(f.read())
            buffer.seek(0)
            return buffer

        finally:
            # Clean up temporary files
            if os.path.exists(temp_md_path):
                os.unlink(temp_md_path)
            if os.path.exists(temp_docx_path):
                os.unlink(temp_docx_path)
