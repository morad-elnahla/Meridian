"""
state.py
--------
Defines the shared "memory" that flows between every agent in the LangGraph
graph. Think of it as a shared clipboard: each agent reads what it needs
from it and writes its own results back onto it before passing it along.

Using a TypedDict (instead of loose dicts) means every agent function gets
autocomplete + type-checking on state fields, which prevents silly bugs
like typos in dictionary keys.
"""

from typing import TypedDict, List, Optional


class SourceDocument(TypedDict):
    """A single piece of evidence collected during research (a news article,
    a financial snippet, etc.). Every claim in the final report should be
    traceable back to one of these."""
    title: str
    url: str
    snippet: str
    source_type: str  # "news" | "financial" | "competitor"


class ResearchState(TypedDict, total=False):
    """
    The full state object passed between LangGraph nodes.
    `total=False` means no field is required upfront — each agent adds its
    own piece as the graph progresses, so the object grows step by step.
    """

    # --- Input ---
    company_name: str          # e.g. "Tesla"
    ticker: Optional[str]      # e.g. "TSLA", optional — user may not know it

    # --- Research Agent output ---
    news_summary: str
    news_sources: List[SourceDocument]

    # --- Financial Agent output ---
    financial_summary: str
    financial_metrics: dict

    # --- Competitor Agent output ---
    competitor_summary: str
    competitor_sources: List[SourceDocument]

    # --- Report Writer output ---
    final_report: str

    # --- Bookkeeping (used by the Streamlit UI to show live progress) ---
    current_step: str          # e.g. "researching", "analyzing_financials"
    errors: List[str]          # any non-fatal errors collected along the way
