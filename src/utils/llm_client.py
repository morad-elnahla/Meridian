"""
llm_client.py
-------------
Single place that builds the Groq LLM client. Every agent imports
`get_llm()` from here instead of constructing its own client, so model
name / temperature changes only need to happen in config.py.
"""

from langchain_groq import ChatGroq

from config import GROQ_API_KEY, GROQ_MODEL, LLM_TEMPERATURE


def get_llm(temperature: float = LLM_TEMPERATURE) -> ChatGroq:
    """Returns a configured ChatGroq client ready to use in an agent."""
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=temperature,
    )
