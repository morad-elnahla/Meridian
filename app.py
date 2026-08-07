"""
app.py
------
Streamlit front-end for Meridian, the Agentic Business Research Analyst.

Run with:
    streamlit run app.py
"""

import html
import time
from datetime import datetime

import streamlit as st

from config import validate_keys
from src.graph import stream_research
from src.utils.export import save_markdown, save_pdf
from src.utils.markdown_render import split_into_sections

st.set_page_config(
    page_title="Meridian | AI Business Research Analyst",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_html(markup: str) -> None:
    compact = "".join(line.strip() for line in markup.splitlines())
    st.markdown(compact, unsafe_allow_html=True)


def load_stylesheet() -> None:
    with open("assets/style.css", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Icons (inline SVG, stroke = currentColor so they inherit their container's
# text color for free - active/hover states are pure CSS, no icon swapping).
# --------------------------------------------------------------------------

ICONS = {
    "home": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11.5 12 4l8 7.5"/><path d="M6 10v9h5v-5.5h2V19h5v-9"/></svg>',
    "signal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17 10 11l3.5 3.5L20 7"/><path d="M14.5 7H20v5.5"/></svg>',
    "compass-link": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="12" r="2.2"/><circle cx="16" cy="12" r="2.2"/><path d="M10.2 12h3.6"/></svg>',
}


def render_sidebar() -> None:
    """Left navigation rail: brand + nav only. Market Signal / Latest News /
    Competitive Landscape / Citations were removed from here since they
    didn't link anywhere - that content lives in the preview cards on the
    Research Desk instead. The Premium Plan upsell and member footer were
    dropped too; they were pure decoration with no function."""
    nav_items = [
        ("home", "Research Desk", True),
    ]

    def nav_html(items):
        rows = []
        for icon_key, label, active in items:
            cls = "mrd-nav-item active" if active else "mrd-nav-item"
            rows.append(f'<a class="{cls}" href="#">{ICONS[icon_key]}{label}</a>')
        return "".join(rows)

    with st.sidebar:
        render_html(
            f"""
            <div class="mrd-sidebar-brand">
                <div class="mrd-mark-side" aria-hidden="true">
                    <svg viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="22" cy="22" r="17" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M22 5.5L26.4 17.6L38.5 22L26.4 26.4L22 38.5L17.6 26.4L5.5 22L17.6 17.6L22 5.5Z" stroke="currentColor" stroke-width="1.5"/>
                        <circle cx="22" cy="22" r="3" fill="currentColor"/>
                    </svg>
                </div>
                <div>
                    <div class="mrd-wordmark-side">Meridian</div>
                    <div class="mrd-brand-sub-side">AI Business Research Analyst</div>
                </div>
            </div>
            <nav class="mrd-nav">{nav_html(nav_items)}</nav>
            """
        )


def render_hero() -> None:
    mountain_svg = """
    <div class="mrd-hero-illustration" aria-hidden="true">
        <svg viewBox="0 0 420 220" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="mrdSun" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="#ad6434" stop-opacity="0.22"/>
                    <stop offset="100%" stop-color="#ad6434" stop-opacity="0"/>
                </radialGradient>
            </defs>
            <circle cx="280" cy="60" r="70" fill="url(#mrdSun)"/>
            <path d="M100 200 165 105 200 150 232 118 285 200Z" fill="#ad6434" opacity="0.14"/>
            <path d="M40 205 140 95 190 155 245 110 360 205Z" fill="#ad6434" opacity="0.20"/>
            <path d="M-10 212 80 130 150 175 220 132 420 212Z" fill="#ad6434" opacity="0.30"/>
            <path d="M20 210 Q160 178 420 210" stroke="#ad6434" stroke-width="1.2" fill="none" opacity="0.22"/>
        </svg>
    </div>
    """
    render_html(
        f"""
        <div class="mrd-hero-wrap">
            {mountain_svg}
            <section class="mrd-hero">
                <div class="mrd-eyebrow-pill">Company intelligence with citations</div>
                <h1>Research Desk {ICONS["compass-link"]}</h1>
                <p>Create a cited research brief on any public company. Meridian reads trusted sources, live financial context, and competitive signals, then summarizes what matters.</p>
            </section>
        </div>
        """
    )


def render_preview_card() -> None:
    render_html(
        """
        <div class="mrd-preview-grid">
            <article class="mrd-preview-card">
                <div class="mrd-preview-icon">↗</div>
                <div class="mrd-card-kicker">Market signal</div>
                <h3>Financial and strategic context</h3>
                <p>Summarizes business momentum, financial signals, and current sentiment from trusted sources.</p>
            </article>
            <article class="mrd-preview-card">
                <div class="mrd-preview-icon">▤</div>
                <div class="mrd-card-kicker">Latest news</div>
                <h3>Recent developments</h3>
                <p>Filters recent company events into clear takeaways instead of a noisy news dump.</p>
            </article>
            <article class="mrd-preview-card">
                <div class="mrd-preview-icon">◇</div>
                <div class="mrd-card-kicker">Competitive landscape</div>
                <h3>Position, rivals, and risks</h3>
                <p>Maps competitors and strategic threats into a concise, cited research brief.</p>
            </article>
        </div>
        <div class="mrd-bottom-tabs">
            <div class="mrd-bottom-tab active">Citations</div>
            <div class="mrd-bottom-tab">News</div>
            <div class="mrd-bottom-tab">Filings</div>
            <div class="mrd-bottom-tab">Financials</div>
            <div class="mrd-bottom-tab">Competitors</div>
            <div class="mrd-bottom-tab">Web sources</div>
        </div>
        """
    )


def render_progress(progress_placeholder, completed_steps: list[str], current_node: str) -> None:
    step_labels = {
        "research": "Researching recent news",
        "financials": "Analyzing financials",
        "competitors": "Mapping competitive landscape",
        "report_writer": "Writing final report",
    }

    lines = ['<div class="mrd-progress-card"><div class="mrd-card-kicker">Working</div>']
    for key, label in step_labels.items():
        if key in completed_steps:
            lines.append(f'<div class="mrd-step done"><span></span>{label} - done</div>')
        elif key == current_node:
            lines.append(f'<div class="mrd-step active"><span></span>{label}...</div>')
        else:
            lines.append(f'<div class="mrd-step"><span></span>{label}</div>')
    lines.append("</div>")
    progress_placeholder.markdown("".join(lines), unsafe_allow_html=True)


def render_report(result: dict) -> None:
    report_text = result["final_report"]
    sections = split_into_sections(report_text)
    all_sources = (result.get("news_sources") or []) + (result.get("competitor_sources") or [])

    word_count = len(report_text.split())
    elapsed = st.session_state.elapsed_seconds
    time_label = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed else "-"

    render_html(
        f"""
        <div class="mrd-report-head">
            <div>
                <div class="mrd-card-kicker">Research brief</div>
                <h2>{html.escape(result["company_name"])} - Research Report</h2>
            </div>
            <span>Generated {datetime.now().strftime("%b %d, %Y · %H:%M")}</span>
        </div>
        """
    )

    stat_cols = st.columns(4)
    stats = [
        (str(len(all_sources)), "Sources cited"),
        (str(len(sections)), "Sections"),
        (f"{word_count:,}", "Words"),
        (time_label, "Research time"),
    ]
    for col, (value, label) in zip(stat_cols, stats):
        with col:
            render_html(
                f"""
                <div class="mrd-metric">
                    <strong>{value}</strong>
                    <span>{label}</span>
                </div>
                """
            )

    if sections:
        tabs = st.tabs([section["title"] for section in sections])
        for tab, section in zip(tabs, sections):
            with tab:
                st.markdown(
                    f'<div class="mrd-tab-panel">{section["body_html"]}</div>',
                    unsafe_allow_html=True,
                )

    if all_sources:
        st.markdown('<div class="mrd-section-label">Citations</div>', unsafe_allow_html=True)
        pills = []
        for source in all_sources:
            url = source.get("url")
            title = source.get("title")
            if not url or not title:
                continue
            pills.append(
                f'<a class="mrd-source" href="{html.escape(url)}" target="_blank">'
                f'{html.escape(title[:48])}</a>'
            )
        st.markdown("".join(pills), unsafe_allow_html=True)

    if result.get("errors"):
        with st.expander("Notes on data gaps"):
            for err in result["errors"]:
                st.caption(f"- {err}")

    st.markdown('<div class="mrd-section-label">Export</div>', unsafe_allow_html=True)
    dl_col1, dl_col2 = st.columns(2)
    md_path = save_markdown(result["company_name"], result["final_report"])
    pdf_path = save_pdf(result["company_name"], result["final_report"])

    with dl_col1:
        with open(md_path, "rb") as file:
            st.download_button(
                "Download Markdown",
                data=file,
                file_name=md_path.split("/")[-1],
                use_container_width=True,
            )
    with dl_col2:
        with open(pdf_path, "rb") as file:
            st.download_button(
                "Download PDF",
                data=file,
                file_name=pdf_path.split("/")[-1],
                use_container_width=True,
            )


load_stylesheet()

if "result_state" not in st.session_state:
    st.session_state.result_state = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = None

render_sidebar()

missing_key_warnings = validate_keys()
if missing_key_warnings:
    for warning in missing_key_warnings:
        st.warning(warning)

render_hero()

with st.form("research_desk", border=False):
    render_html(
        f"""
        <div class="mrd-form-head">
            <div class="mrd-form-head-lockup">
                <div class="mrd-form-icon">{ICONS["signal"]}</div>
                <div>
                    <h2>New research brief</h2>
                </div>
            </div>
            <p>Start with a company name. Add a ticker when you want cleaner financial lookup.</p>
        </div>
        """
    )
    form_col1, form_col2, form_col3 = st.columns([2.2, 1, 1])
    with form_col1:
        company_name = st.text_input(
            "Company name",
            placeholder="e.g. Microsoft Corporation",
        )
    with form_col2:
        ticker = st.text_input(
            "Ticker",
            placeholder="e.g. MSFT",
        )
    with form_col3:
        run_clicked = st.form_submit_button("Generate brief →", use_container_width=True)

    st.markdown('<div class="mrd-section-label">Sources</div>', unsafe_allow_html=True)
    source_cols = st.columns(6)
    sources = [
        "SEC filings",
        "News",
        "Earnings",
        "Financials",
        "Competitors",
        "Web",
    ]
    for col, source in zip(source_cols, sources):
        with col:
            st.checkbox(source, value=source != "Web")

result_slot = st.empty()

if run_clicked:
    if not company_name.strip():
        st.error("Please enter a company name first.")
    else:
        st.session_state.result_state = None
        st.session_state.is_running = True

        progress_placeholder = result_slot.empty()
        completed_steps = []
        start_time = time.time()

        try:
            for node_name, updated_state in stream_research(
                company_name.strip(), ticker.strip() or None
            ):
                if node_name not in completed_steps:
                    completed_steps.append(node_name)

                render_progress(progress_placeholder, completed_steps, node_name)
                st.session_state.result_state = updated_state

            st.session_state.elapsed_seconds = time.time() - start_time
        except Exception as exc:
            st.error(
                "Something went wrong while running the research pipeline. "
                f"Details: {exc}"
            )
        finally:
            st.session_state.is_running = False
            st.rerun()

with result_slot.container():
    result = st.session_state.result_state
    if result and result.get("final_report"):
        render_report(result)
    else:
        render_preview_card()