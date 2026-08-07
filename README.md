Here's a polished, professional version — added badges, a features section, tech-stack table, troubleshooting, and tightened up the structure. Pasting the code, not creating a file, like last time:

```markdown
# 🧭 Meridian — Agentic Business Research Analyst

<p align="center">
  <em>A multi-agent AI system that turns a company name into a cited, decision-ready research brief — in seconds, not hours.</em>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="LangGraph" src="https://img.shields.io/badge/Orchestration-LangGraph-1C3C3C">
  <img alt="Groq" src="https://img.shields.io/badge/LLM-Groq%20Llama%203.3-F55036">
  <img alt="ChromaDB" src="https://img.shields.io/badge/Vector%20DB-ChromaDB-6A3DE8">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

---

## Table of contents

- [Why this project](#why-this-project)
- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Design notes](#design-notes)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Why this project

Investment, consulting, and procurement teams routinely need a fast first pass on a company before a call, a deal, or a pitch. Meridian automates that first pass: it researches, cross-checks the findings against a local knowledge base (RAG), and writes a cited, decision-ready report — recent news, financial snapshot, and competitive landscape — the way a junior analyst would.

## Features

- 🔍 **Multi-agent research** — dedicated agents for news, financials, and competitors, orchestrated as a LangGraph state graph
- 📚 **Grounded in real sources (RAG)** — every snippet the agents collect is embedded into ChromaDB before the report is written, so nothing is hallucinated from thin air
- 📈 **Live financial data** — pulled directly from Yahoo Finance via `yfinance`
- 🧠 **Fast inference** — Groq's `llama-3.3-70b-versatile` for low-latency report generation
- 📄 **Export-ready** — one click to Markdown or PDF
- 🛡️ **Graceful degradation** — a missing ticker or a rate-limited API doesn't crash the run; gaps are surfaced in the report instead of hidden
- 🖥️ **Clean, branded UI** — custom Streamlit stylesheet, no default Streamlit look

## Architecture

```
                 ┌────────────────┐
   company name  │   LangGraph    │
   + ticker  ───▶│  Orchestrator  │
                 └───────┬────────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
  Research Agent   Financial Agent   Competitor Agent
  (Tavily search)  (yfinance)        (Tavily search)
        │                │                 │
        └────────────────┼─────────────────┘
                         ▼
                 Chroma Vector Store  (RAG)
                         │
                         ▼
                 Report Writer Agent
                 (retrieves + synthesizes)
                         │
                         ▼
                 Final Markdown Report
                 (+ PDF / Markdown export)
```

- **Orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph) — a directed state graph where each agent is a node and a shared `ResearchState` object is passed between them.
- **RAG / Vector DB:** [ChromaDB](https://www.trychroma.com/), running fully locally with `sentence-transformers` embeddings — no extra API key needed. Every snippet the agents collect is embedded and stored; the Report Writer retrieves the most relevant chunks before writing each section, so the final report stays grounded in real sources.
- **Tool calling:** Tavily (web search) and yfinance (market data), wrapped as clean tool classes in `src/tools/`.
- **LLM:** Groq (`llama-3.3-70b-versatile` by default) via `langchain-groq`.
- **UI:** Streamlit, with a small custom stylesheet for a clean, branded look.

## Tech stack

| Layer          | Technology                                | Purpose                                  |
|----------------|--------------------------------------------|-------------------------------------------|
| Orchestration  | LangGraph                                  | Multi-agent state graph                   |
| LLM            | Groq (`llama-3.3-70b-versatile`)           | Report generation                         |
| Web search     | Tavily                                     | News & competitor research                |
| Financial data | yfinance                                   | Live market/financial snapshot            |
| RAG            | ChromaDB + sentence-transformers           | Grounding report content in real sources  |
| UI             | Streamlit                                  | Front end                                 |
| Export         | Markdown / PDF                             | Shareable deliverables                    |

## Project structure

```
biz-research-analyst/
├── app.py                     # Streamlit UI entry point
├── config.py                  # All settings, paths, API keys in one place
├── requirements.txt
├── .env.example
├── src/
│   ├── state.py                 # Shared LangGraph state schema
│   ├── graph.py                 # Builds and runs the LangGraph pipeline
│   ├── agents/
│   │   ├── research_agent.py
│   │   ├── financial_agent.py
│   │   ├── competitor_agent.py
│   │   └── report_writer_agent.py
│   ├── tools/
│   │   ├── web_search_tool.py   # Tavily wrapper
│   │   └── financial_tool.py    # yfinance wrapper
│   ├── rag/
│   │   └── vector_store.py      # Chroma wrapper (embed/store/retrieve)
│   └── utils/
│       ├── llm_client.py        # Shared Groq client builder
│       └── export.py            # Markdown / PDF export
└── assets/
    └── style.css                 # Brand stylesheet for Streamlit
```

## Setup

**1. Clone and create a virtual environment**

```bash
git clone <your-repo-url>
cd biz-research-analyst
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Add your API keys**

```bash
cp .env.example .env
```

Then open `.env` and fill in:

| Key              | Where to get it                          | Free tier? |
|-------------------|-------------------------------------------|------------|
| `GROQ_API_KEY`    | https://console.groq.com                  | ✅ Yes      |
| `TAVILY_API_KEY`  | https://tavily.com                        | ✅ Yes      |

**3. Run the app**

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Usage

Enter a company name (e.g. `Tesla`) with its ticker (`TSLA`) and click **Generate brief**. Meridian will:

1. Research recent news via Tavily
2. Pull live financials via yfinance
3. Map the competitive landscape against peers
4. Embed everything into a fresh ChromaDB collection
5. Generate a cited report you can export as Markdown or PDF

## Design notes

- **Sequential graph, parallel-ready.** Research, Financial, and Competitor agents don't depend on each other's output, only on the original input — the graph runs them sequentially for clearer live progress in the UI, but the structure in `src/graph.py` makes it straightforward to branch them in parallel later.
- **Graceful degradation.** If a ticker isn't provided, or Tavily/Groq rate limits are hit, each agent still returns a usable (if partial) result instead of crashing the whole pipeline — gaps are surfaced to the user instead of hidden.
- **Fresh vector store per session.** Each analysis creates its own Chroma collection (named after the company) so results from different runs never mix.

## Roadmap

- [ ] Parallelize the Research / Financial / Competitor agents
- [ ] Multi-company comparison reports
- [ ] Persistent report history / saved briefs
- [ ] Configurable LLM provider (OpenAI / Anthropic as alternatives to Groq)

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `GROQ_API_KEY not found` | `.env` missing or not filled in | Run `cp .env.example .env` and add your key |
| Empty / partial financial section | Invalid or missing ticker | Double-check the ticker symbol on Yahoo Finance |
| Report has few citations | Tavily rate limit hit | Wait a minute and re-run, or check your Tavily usage dashboard |
| `ModuleNotFoundError` on launch | Virtual env not activated | Re-run `source venv/bin/activate` before `streamlit run app.py` |

## License

MIT — see `LICENSE` for details.
```
