"""
web_search_tool.py
-------------------
Wraps the Tavily search API so the Research and Competitor agents can pull
fresh, real-world information from the web. Tavily is used (instead of a
raw Google scrape) because it returns clean, LLM-ready snippets and is
built specifically for AI agent use cases.
"""

from tavily import TavilyClient

from config import TAVILY_API_KEY
from src.state import SourceDocument


class WebSearchTool:
    """A minimal, agent-friendly wrapper around Tavily search."""

    def __init__(self):
        if not TAVILY_API_KEY:
            self.client = None
        else:
            self.client = TavilyClient(api_key=TAVILY_API_KEY)

    def search(self, query: str, max_results: int = 5, source_type: str = "news") -> list[SourceDocument]:
        """
        Run a web search and return results shaped as SourceDocument dicts,
        so every downstream agent can treat search results and RAG chunks
        the same way.
        """
        if self.client is None:
            # No API key configured — fail gracefully instead of crashing
            # the whole pipeline. The UI surfaces this as a warning.
            return []

        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
            )
        except Exception as exc:
            # Network hiccups / rate limits shouldn't kill the whole run —
            # we just return no results and let the agent note the gap.
            print(f"[WebSearchTool] Tavily search failed for '{query}': {exc}")
            return []

        documents: list[SourceDocument] = []
        for result in response.get("results", []):
            documents.append(
                SourceDocument(
                    title=result.get("title", "Untitled"),
                    url=result.get("url", ""),
                    snippet=result.get("content", "")[:800],  # keep chunks manageable
                    source_type=source_type,
                )
            )
        return documents
