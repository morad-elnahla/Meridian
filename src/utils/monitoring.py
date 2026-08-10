"""
monitoring.py
--------------
Lightweight, dependency-free observability for a single research run.

Tracks two things per LangGraph node (research / financials / competitors /
report_writer):
  1. Wall-clock time spent in that node.
  2. LLM token usage + an estimated USD cost for every Groq call made inside it.

Everything is written onto the shared `ResearchState` dict as the graph
runs, so by the time `report_writer_agent` finishes, `state["timings"]` and
`state["token_usage"]` contain a full per-node breakdown, and
`state["total_time_s"]` / `state["total_cost_usd"]` hold the run totals.
The Streamlit UI can render these directly — no external tracing service,
no extra API key, works the same locally and on Streamlit Community Cloud.

Cost is an ESTIMATE based on the per-token rates in config.py, not billed
usage pulled from Groq's dashboard. Update GROQ_PRICE_PER_M_INPUT_TOKENS /
GROQ_PRICE_PER_M_OUTPUT_TOKENS in config.py if Groq's pricing changes.
"""

import time
from contextlib import contextmanager

from config import GROQ_PRICE_PER_M_INPUT_TOKENS, GROQ_PRICE_PER_M_OUTPUT_TOKENS


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Rough USD cost for one LLM call, given token counts and the
    configured per-million-token rates."""
    input_cost = (input_tokens / 1_000_000) * GROQ_PRICE_PER_M_INPUT_TOKENS
    output_cost = (output_tokens / 1_000_000) * GROQ_PRICE_PER_M_OUTPUT_TOKENS
    return round(input_cost + output_cost, 6)


def _extract_usage(response) -> tuple[int, int]:
    """
    Pull (input_tokens, output_tokens) out of a LangChain AIMessage.
    Different provider integrations / langchain-core versions expose usage
    in slightly different places, so we check both known conventions
    instead of assuming one and silently reporting zero cost.
    """
    usage = getattr(response, "usage_metadata", None)
    if usage:
        return usage.get("input_tokens", 0), usage.get("output_tokens", 0)

    meta = getattr(response, "response_metadata", {}) or {}
    token_usage = meta.get("token_usage", {})
    return token_usage.get("prompt_tokens", 0), token_usage.get("completion_tokens", 0)


def track_llm_call(llm, messages, state, node_name: str):
    """
    Drop-in replacement for `llm.invoke(messages)`. Behaves identically
    (returns the same AIMessage) but additionally records token usage and
    estimated cost onto `state["token_usage"][node_name]`, and rolls it
    into `state["total_cost_usd"]`.

    A node can call this more than once (e.g. a future retry) — usage
    accumulates rather than overwrites.
    """
    response = llm.invoke(messages)

    input_tokens, output_tokens = _extract_usage(response)
    cost = estimate_cost(input_tokens, output_tokens)

    node_usage = state.setdefault("token_usage", {}).setdefault(
        node_name, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    )
    node_usage["input_tokens"] += input_tokens
    node_usage["output_tokens"] += output_tokens
    node_usage["cost_usd"] = round(node_usage["cost_usd"] + cost, 6)

    state["total_cost_usd"] = round(state.get("total_cost_usd", 0.0) + cost, 6)

    return response


@contextmanager
def track_node_time(state, node_name: str):
    """
    Context manager: wrap a node's body in `with track_node_time(state, "research"):`
    to record how many seconds it took in `state["timings"][node_name]`,
    and add it to the running `state["total_time_s"]`.

    Uses try/finally so the timing is still recorded even if the node
    raises — useful for spotting which agent is slow right before it fails.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = round(time.perf_counter() - start, 2)
        state.setdefault("timings", {})[node_name] = elapsed
        state["total_time_s"] = round(state.get("total_time_s", 0.0) + elapsed, 2)