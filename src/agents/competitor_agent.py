"""
competitor_agent.py
--------------------
Searches the web for the company's main competitors and how it's
positioned against them, then summarizes the competitive landscape.
Runs independently of the Financial agent so a missing ticker never blocks
this section of the report.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from config import MAX_COMPETITOR_RESULTS
from src.state import ResearchState
from src.tools.web_search_tool import WebSearchTool
from src.utils.llm_client import get_llm

SYSTEM_PROMPT = """You are a competitive intelligence analyst. Given raw
web snippets about a company's market and competitors, write a concise
(120-200 word) summary of the competitive landscape: who the main
competitors are and how the company is positioned against them. Stay
strictly grounded in the provided snippets."""


def competitor_agent(state: ResearchState, vector_store) -> ResearchState:
    """
    LangGraph node function. Searches for competitor/market-positioning
    information and writes `competitor_summary` + `competitor_sources`
    back onto the state.
    """
    company_name = state["company_name"]
    state["current_step"] = "analyzing_competitors"

    search_tool = WebSearchTool()
    sources = search_tool.search(
        query=f"{company_name} main competitors market position vs rivals",
        max_results=MAX_COMPETITOR_RESULTS,
        source_type="competitor",
    )

    if not sources:
        state["competitor_summary"] = (
            "No competitor information could be retrieved. This section is inconclusive."
        )
        state["competitor_sources"] = []
        state.setdefault("errors", []).append("Competitor agent: no sources found.")
        return state

    vector_store.add_documents(
        texts=[s["snippet"] for s in sources],
        metadatas=[{"title": s["title"], "url": s["url"], "source": "competitor"} for s in sources],
    )

    combined_snippets = "\n\n".join(f"- {s['title']}: {s['snippet']}" for s in sources)

    llm = get_llm()
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Company: {company_name}\n\nRaw snippets:\n{combined_snippets}"),
        ]
    )

    state["competitor_summary"] = response.content
    state["competitor_sources"] = sources
    return state
