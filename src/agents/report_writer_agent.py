"""
report_writer_agent.py
-----------------------
The final agent in the pipeline. It does NOT just concatenate the other
agents' summaries — it uses the RAG layer (vector store) to retrieve the
most relevant supporting evidence for each section, then asks the LLM to
write a polished, cited final report. This is the step where the "R" in
RAG actually earns its keep: grounding the final narrative in retrievable
source snippets rather than the summaries alone.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from src.state import ResearchState
from src.utils.llm_client import get_llm
from src.utils.monitoring import track_llm_call, track_node_time

SYSTEM_PROMPT = """You are a senior business research analyst writing a
final report for a client (e.g. a VC firm or corporate strategy team).

You will be given:
1. Draft summaries from three research agents (news, financials, competitors)
2. Supporting evidence snippets retrieved from a knowledge base

Write a well-structured Markdown report with these sections:
## Executive Summary
## Recent Developments
## Financial Snapshot
## Competitive Landscape
## Key Risks & Opportunities

Rules:
- Stay strictly grounded in the provided summaries and evidence. Never invent facts.
- Where a specific evidence snippet supports a claim, you may reference it naturally (e.g. "according to recent reporting...").
- Keep the tone professional, concise, and decision-useful.
- If a section has little or no data, say so honestly instead of padding it.
"""


def report_writer_agent(state: ResearchState, vector_store) -> ResearchState:
    """
    LangGraph node function. Retrieves supporting evidence from the vector
    store for each report section, then synthesizes everything the earlier
    agents produced into one final Markdown report.
    """
    state["current_step"] = "writing_report"
    company_name = state["company_name"]

    with track_node_time(state, "report_writer"):
        # RAG retrieval: pull the most relevant evidence chunks per section
        # instead of dumping every source into the prompt (keeps it grounded
        # AND keeps the prompt small).
        news_evidence = vector_store.query(f"{company_name} recent news and strategy")
        financial_evidence = vector_store.query(f"{company_name} financial performance")
        competitor_evidence = vector_store.query(f"{company_name} competitors market position")

        def format_evidence(chunks: list[dict]) -> str:
            if not chunks:
                return "(no supporting evidence retrieved)"
            return "\n".join(f"- {c['metadata'].get('title', 'source')}: {c['text'][:300]}" for c in chunks)

        prompt_body = f"""
Company: {company_name}

--- DRAFT SUMMARIES ---
News summary: {state.get('news_summary', 'N/A')}
Financial summary: {state.get('financial_summary', 'N/A')}
Competitor summary: {state.get('competitor_summary', 'N/A')}

--- RETRIEVED EVIDENCE (News) ---
{format_evidence(news_evidence)}

--- RETRIEVED EVIDENCE (Financial) ---
{format_evidence(financial_evidence)}

--- RETRIEVED EVIDENCE (Competitors) ---
{format_evidence(competitor_evidence)}
"""

        llm = get_llm(temperature=0.3)
        response = track_llm_call(
            llm,
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt_body),
            ],
            state,
            "report_writer",
        )

        state["final_report"] = response.content

    state["current_step"] = "done"
    return state