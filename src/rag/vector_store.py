"""
vector_store.py
----------------
The RAG (Retrieval-Augmented Generation) layer of the project.

Every piece of evidence the agents collect (news snippets, competitor
mentions, financial notes) gets embedded and stored in a local Chroma
vector database. Later, the Report Writer agent queries this store to pull
back only the most relevant chunks before writing each section of the
report — this is what keeps the final report grounded in real sources
instead of the LLM "making things up".

The store is created fresh for each company research session (collection
name = company name), so results from one analysis never leak into another.
"""

import re
import chromadb
from chromadb.utils import embedding_functions

from config import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME, VECTOR_STORE_TOP_K


def _slugify(text: str) -> str:
    """Turn 'Tesla, Inc.' into 'tesla-inc' so it's a safe Chroma collection name."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "session"


class ResearchVectorStore:
    """
    Thin wrapper around a local Chroma collection dedicated to a single
    research session (one company). Handles embedding + storing text chunks,
    and retrieving the most relevant ones for a given query.
    """

    def __init__(self, company_name: str):
        self.client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))

        # Local, offline embedding model — no API key needed, works even if
        # Groq/Tavily quotas are exhausted.
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )

        collection_name = f"session-{_slugify(company_name)}"

        # Start every session with a clean collection so old data from a
        # previous company never pollutes a new report.
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass  # Collection didn't exist yet — nothing to clean up.

        self.collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self.embedder,
        )
        self._doc_counter = 0

    def add_documents(self, texts: list[str], metadatas: list[dict]) -> None:
        """
        Embed and store a batch of text chunks.
        `metadatas` should be the same length as `texts`, one dict per chunk
        (e.g. {"source": "news", "title": "...", "url": "..."}).
        """
        if not texts:
            return

        ids = [f"doc-{self._doc_counter + i}" for i in range(len(texts))]
        self._doc_counter += len(texts)

        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def query(self, query_text: str, top_k: int = VECTOR_STORE_TOP_K) -> list[dict]:
        """
        Retrieve the top_k chunks most relevant to `query_text`.
        Returns a list of {"text": ..., "metadata": ...} dicts, ordered by
        relevance (closest match first).
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(top_k, self.collection.count()),
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        return [{"text": doc, "metadata": meta} for doc, meta in zip(docs, metas)]
