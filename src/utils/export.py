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

    # The built-in "Helvetica" font only supports latin-1 (256 chars). Any
    # character outside that range - e.g. the euro sign - would crash fpdf2
    # with FPDFUnicodeEncodingException, so map the common offenders to their
    # plain ASCII equivalents before rendering. Anything still unsupported
    # gets silently dropped so the PDF always renders instead of blowing up.
    _UNICODE_REPLACEMENTS = {
        "\u20ac": "EUR",   # € euro sign
        "\u201c": '"',     # left double quote
        "\u201d": '"',     # right double quote
        "\u2018": "'",     # left single quote
        "\u2019": "'",     # right single quote / apostrophe
        "\u2014": "-",     # em dash
        "\u2013": "-",     # en dash
        "\u2026": "...",   # ellipsis
        "\u2122": "(TM)",  # trademark
        "\u00a9": "(c)",   # copyright
        "\u00ae": "(R)",   # registered
        "\u00b0": "deg",   # degree sign
    }

    def _sanitize(text: str) -> str:
        for char, replacement in _UNICODE_REPLACEMENTS.items():
            text = text.replace(char, replacement)
        # Drop any remaining character outside latin-1 to be safe.
        return "".join(ch for ch in text if ord(ch) < 256)

    for line in report_text.split("\n"):
        clean_line = _sanitize(re.sub(r"[*_`#]", "", line)).strip()
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
