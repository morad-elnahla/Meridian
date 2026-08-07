"""
financial_agent.py
-------------------
Pulls real market data for the company (if a ticker is available) and asks
the LLM to translate the raw numbers into a short, plain-English financial
health summary. This agent is intentionally decoupled from the ticker
lookup — if the user didn't supply one, it degrades gracefully instead of
crashing the whole graph.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from src.state import ResearchState
from src.tools.financial_tool import FinancialDataTool
from src.utils.llm_client import get_llm

SYSTEM_PROMPT = """You are a financial analyst. Given a set of raw
financial metrics for a company, write a concise (100-180 words) plain
-English summary of its financial health: valuation, profitability, and
growth trend. Only use the numbers provided — do not invent figures.
If a metric is missing, simply skip it rather than guessing."""


def financial_agent(state: ResearchState, vector_store) -> ResearchState:
    """
    LangGraph node function. Reads `ticker` from state (if present), fetches
    live metrics via yfinance, summarizes them, and writes
    `financial_summary` + `financial_metrics` back onto the state.
    """
    state["current_step"] = "analyzing_financials"
    ticker = state.get("ticker")

    if not ticker:
        state["financial_summary"] = (
            "No stock ticker was provided, so live financial data could not "
            "be retrieved for this company."
        )
        state["financial_metrics"] = {}
        return state

    fin_tool = FinancialDataTool()
    metrics = fin_tool.get_metrics(ticker)

    if not metrics:
        state["financial_summary"] = (
            f"No financial data was found for ticker '{ticker}'. It may be "
            "delisted, private, or the ticker symbol may be incorrect."
        )
        state["financial_metrics"] = {}
        state.setdefault("errors", []).append(f"Financial agent: no data for ticker '{ticker}'.")
        return state

    # Push a text version of the metrics into the vector store too, so the
    # Report Writer can retrieve financial context alongside news context.
    metrics_text = "\n".join(f"{k}: {v}" for k, v in metrics.items() if v is not None)
    vector_store.add_documents(
        texts=[metrics_text],
        metadatas=[{"title": f"{ticker} financial snapshot", "url": "", "source": "financial"}],
    )

    llm = get_llm()
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Ticker: {ticker}\n\nRaw metrics:\n{metrics_text}"),
        ]
    )

    state["financial_summary"] = response.content
    state["financial_metrics"] = metrics
    return state
