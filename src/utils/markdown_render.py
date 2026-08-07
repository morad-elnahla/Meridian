"""
markdown_render.py
-------------------
Turns the LLM-generated Markdown report into a list of section dicts the
Streamlit UI can render as styled cards, instead of dumping raw Markdown
into st.markdown(). Deliberately dependency-free (no `markdown` package)
since the report writer's output only ever uses a small, predictable
subset of Markdown: "## " headings, paragraphs, **bold**, and "- " bullet
lists. A tiny hand-rolled converter is easier to reason about than pulling
in a general-purpose Markdown engine for that subset.
"""

import html
import re


def split_into_sections(report_markdown: str) -> list[dict]:
    """
    Splits a Markdown report into sections at each "## " heading.
    Returns a list of {"title": str, "body_html": str} dicts, in order.
    Any text before the first "## " heading is dropped (the report writer
    prompt always starts with a heading, so this is just a safety net).
    """
    # Split on lines that start with "## " (but not "### ") while keeping
    # the heading text itself.
    parts = re.split(r"(?m)^##\s+(.+)$", report_markdown)

    # re.split with a capturing group returns:
    # [text_before_first_match, heading1, body1, heading2, body2, ...]
    sections = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append({"title": title, "body_html": _markdown_block_to_html(body)})

    return sections


def _markdown_block_to_html(text: str) -> str:
    """Converts a chunk of simple Markdown (paragraphs, **bold**, "- " lists)
    into HTML. Escapes everything else so LLM output can never inject
    arbitrary HTML into the page.

    Works line-by-line (not just block-by-block) because the LLM often
    writes a lead-in sentence directly above a bullet list with no blank
    line in between, e.g.:
        Key points:
        - New factory in Mexico
        - Continued FSD rollout
    A pure block-level split would treat that whole chunk as one failed
    "is this a list?" check and flatten it into a single paragraph — so
    instead we walk line by line and open/close <p>/<ul> as the line type
    changes.
    """
    lines = [line.strip() for line in text.strip().split("\n")]

    html_parts = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []

    def flush_paragraph():
        if paragraph_lines:
            joined = " ".join(paragraph_lines)
            html_parts.append(f"<p>{_inline_markdown(joined)}</p>")
            paragraph_lines.clear()

    def flush_list():
        if list_items:
            items_html = "".join(f"<li>{_inline_markdown(item)}</li>" for item in list_items)
            html_parts.append(f"<ul>{items_html}</ul>")
            list_items.clear()

    for line in lines:
        if not line:
            # Blank line: paragraph break, but doesn't end an in-progress list.
            flush_paragraph()
            continue

        if line.startswith(("- ", "* ")):
            flush_paragraph()
            list_items.append(line[2:].strip())
        else:
            flush_list()
            paragraph_lines.append(line)

    flush_paragraph()
    flush_list()

    return "".join(html_parts)


def _inline_markdown(text: str) -> str:
    """Escapes HTML first (safety), then re-applies just **bold** support."""
    escaped = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
