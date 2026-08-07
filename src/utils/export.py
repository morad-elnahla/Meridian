"""
export.py
---------
Turns the final Markdown report into downloadable files (Markdown + PDF)
that the Streamlit UI can offer as download buttons.
"""

import re
from datetime import datetime

from fpdf import FPDF

from config import EXPORTS_DIR


def save_markdown(company_name: str, report_text: str) -> str:
    """Writes the report to a .md file and returns the file path."""
    filename = f"{_safe_filename(company_name)}_report.md"
    path = EXPORTS_DIR / filename
    path.write_text(report_text, encoding="utf-8")
    return str(path)


def save_pdf(company_name: str, report_text: str) -> str:
    """
    Renders a simplified plain-text version of the Markdown report as a
    PDF. This keeps formatting minimal (headings bolded, rest as body
    text) so it works reliably without a full Markdown-to-PDF renderer.
    """
    filename = f"{_safe_filename(company_name)}_report.pdf"
    path = EXPORTS_DIR / filename

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Business Research Report: {company_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 8, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for line in report_text.split("\n"):
        clean_line = re.sub(r"[*_`#]", "", line).strip()
        if not clean_line:
            pdf.ln(3)
            continue

        # NOTE: unlike cell(), multi_cell() does NOT reset the X cursor back
        # to the left margin by default — it leaves it wherever the last
        # line ended. Without `new_x="LMARGIN"` here, the next multi_cell
        # call can start near the right margin and run out of horizontal
        # space entirely. Always pass new_x/new_y explicitly.
        if line.strip().startswith("##"):
            pdf.set_font("Helvetica", "B", 13)
            pdf.ln(3)
            pdf.multi_cell(0, 8, clean_line, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
        else:
            pdf.multi_cell(0, 7, clean_line, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(path))
    return str(path)


def _safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_") or "report"
