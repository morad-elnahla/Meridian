"""
graph.py
--------
Wires the individual agent functions together into a LangGraph state
machine. This is the "orchestrator" — it decides the order agents run in
and passes the shared state between them.

Flow:
    START -> research_agent -> financial_agent -> competitor_agent
          -> report_writer_agent -> END

Research, Financial, and Competitor agents don't depend on each other's
output (only on the original company_name/ticker input), so they could
also be parallelized — this project runs them sequentially for simplicity
and clearer progress reporting in the UI, but the graph structure makes it
easy to switch to parallel branches later.
"""

from functools import partial

from langgraph.graph import StateGraph, END

from src.state import ResearchState
from src.rag.vector_store import ResearchVectorStore
from src.agents.research_agent import research_agent
from src.agents.financial_agent import financial_agent
from src.agents.competitor_agent import competitor_agent
from src.agents.report_writer_agent import report_writer_agent


def build_graph(vector_store: ResearchVectorStore):
    """
    Constructs and compiles the LangGraph state graph.
    `vector_store` is injected here (rather than created inside each agent)
    so every node in this run shares the SAME collection — that's what
    makes the RAG step in report_writer_agent actually see everything the
    earlier agents stored.
    """
    graph = StateGraph(ResearchState)

    # Each node is the agent function with `vector_store` pre-bound via
    # functools.partial, since LangGraph nodes only receive `state`.
    graph.add_node("research", partial(research_agent, vector_store=vector_store))
    graph.add_node("financials", partial(financial_agent, vector_store=vector_store))
    graph.add_node("competitors", partial(competitor_agent, vector_store=vector_store))
    graph.add_node("report_writer", partial(report_writer_agent, vector_store=vector_store))

    graph.set_entry_point("research")
    graph.add_edge("research", "financials")
    graph.add_edge("financials", "competitors")
    graph.add_edge("competitors", "report_writer")
    graph.add_edge("report_writer", END)

    return graph.compile()


def run_research(company_name: str, ticker: str | None = None) -> ResearchState:
    """
    Convenience entry point: builds a fresh vector store + graph for this
    company and runs the full pipeline to completion. Used by the CLI /
    non-streaming callers. The Streamlit UI uses `stream_research` below
    instead so it can show live per-agent progress.
    """
    vector_store = ResearchVectorStore(company_name)
    compiled_graph = build_graph(vector_store)

    initial_state: ResearchState = {
        "company_name": company_name,
        "ticker": ticker,
        "errors": [],
    }
    return compiled_graph.invoke(initial_state)


def stream_research(company_name: str, ticker: str | None = None):
    """
    Generator version of `run_research`. Yields (node_name, updated_state)
    after each agent finishes, so the Streamlit UI can update a progress
    indicator live instead of freezing until the whole pipeline is done.
    """
    vector_store = ResearchVectorStore(company_name)
    compiled_graph = build_graph(vector_store)

    initial_state: ResearchState = {
        "company_name": company_name,
        "ticker": ticker,
        "errors": [],
    }

    for step_output in compiled_graph.stream(initial_state):
        # step_output looks like {"node_name": <updated_state>}
        for node_name, updated_state in step_output.items():
            yield node_name, updated_state
