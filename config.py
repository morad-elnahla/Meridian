"""
config.py
---------
Single source of truth for every setting the app needs: API keys, model
names, and file-system paths. Every other module imports from here instead
of calling `os.getenv(...)` directly, so if a key name ever changes we only
have to update it in ONE place.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from the local .env file into the process environment.
# This must run before we read any os.getenv() calls below.
load_dotenv()

# --- Project paths -----------------------------------------------------
# BASE_DIR points at the project root, no matter which file imports config.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
EXPORTS_DIR = DATA_DIR / "exports"

# Make sure the folders exist so the app never crashes on first run.
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# --- API keys ------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# --- Model settings --------------------------------------------------
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = 0.2  # Low temperature = more factual, less "creative" drift

# Local embedding model used for the vector store (RAG). Runs on CPU,
# no API key required, so the app still works if Tavily/Groq quotas run out.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# --- Agent behaviour ---------------------------------------------------
MAX_SEARCH_RESULTS = 6          # How many web results the Research agent pulls
MAX_COMPETITOR_RESULTS = 5      # How many competitor mentions to pull
VECTOR_STORE_TOP_K = 4          # How many chunks the Report Writer retrieves per query


def validate_keys() -> list[str]:
    """
    Returns a list of human-readable warnings for any missing API key.
    The UI calls this on startup so the user gets a clear message instead
    of a confusing stack trace halfway through a run.
    """
    warnings = []
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        warnings.append("GROQ_API_KEY is missing — the LLM agents will not be able to run.")
    if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_api_key_here":
        warnings.append("TAVILY_API_KEY is missing — the Research agent will not be able to search the web.")
    return warnings
