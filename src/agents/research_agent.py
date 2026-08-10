"""
research_agent.py
------------------
The first agent in the pipeline. Its job: find out what's currently
happening with the company (recent news, announcements, strategic moves)
and summarize it. Every source it finds is also pushed into the vector
store so the Report Writer can retrieve and cite it later.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from config import MAX_SEARCH_RESULTS
from src.state import ResearchState
from src.tools.web_search_tool import WebSearchTool
from src.utils.llm_client import get_llm
from src.utils.monitoring import track_llm_call, track_node_time

SYSTEM_PROMPT = """You are a meticulous business research analyst.
Given raw news snippets about a company, write a concise, factual summary
(150-250 words) of what is currently happening with the company: recent
announcements, strategic direction, notable events. Stay strictly grounded
in the provided snippets — do not invent facts. Write in a neutral,
professional tone suitable for an investment research report."""


def research_agent(state: ResearchState, vector_store) -> ResearchState:
    """
    LangGraph node function. Reads `company_name` from state, searches the
    web for recent news, summarizes it with the LLM, and writes
    `news_summary` + `news_sources` back onto the state.
    """
    company_name = state["company_name"]
    state["current_step"] = "researching"

    with track_node_time(state, "research"):
        search_tool = WebSearchTool()
        sources = search_tool.search(
            query=f"{company_name} latest news strategy announcements 2026",
            max_results=MAX_SEARCH_RESULTS,
            source_type="news",
        )

        if not sources:
            state["news_summary"] = (
                "No recent news could be retrieved (web search unavailable or "
                "no results found). This section is inconclusive."
            )
            state["news_sources"] = []
            state.setdefault("errors", []).append("Research agent: no news sources found.")
            return state

        # Store every snippet in the vector DB so later agents (Report Writer)
        # can retrieve it with semantic search instead of re-reading everything.
        vector_store.add_documents(
            texts=[s["snippet"] for s in sources],
            metadatas=[{"title": s["title"], "url": s["url"], "source": "news"} for s in sources],
        )

        combined_snippets = "\n\n".join(f"- {s['title']}: {s['snippet']}" for s in sources)

        llm = get_llm()
        response = track_llm_call(
            llm,
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Company: {company_name}\n\nRaw news snippets:\n{combined_snippets}"),
            ],
            state,
            "research",
        )

        state["news_summary"] = response.content
        state["news_sources"] = sources

    return state