"""
monitoring_store.py
-------------------
Disk-backed persistence for the last research run's observability data
(timings, token usage, cost).

Why this exists
~~~~~~~~~~~~~~~
The Streamlit UI keeps the run output ONLY in `st.session_state.result_state`,
which lives in the server's in-memory session. A full page reload or a plain
`<a href="?page=...">` navigation opens a brand-new browser session, so
`result_state` is empty and the Monitoring page shows "No run to show yet" -
even though the run itself recorded timings/cost correctly.

Persisting the monitoring payload to a JSON file means the Monitoring page
keeps working after:
  - full page reloads (F5)
  - opening Monitoring in a new tab
  - closing/reopening the browser
  - server restarts (Streamlit reloads the script, file is still there)

Only the observability fields (timings, token usage, totals) are stored -
the full report is heavy and not needed on the Monitoring page.
"""

import json
from pathlib import Path

from config import DATA_DIR

LAST_RUN_FILE = DATA_DIR / "monitoring_state.json"

# Fields worth keeping for observability. If monitoring.py adds new ones,
# append them here - old files stay readable because .get() handles misses.
MONITORING_KEYS = [
    "timings",
    "token_usage",
    "total_time_s",
    "total_cost_usd",
    "company_name",
]


def save_last_run(state: dict) -> Path:
    """
    Write the monitoring-relevant slice of `state` to disk so the Monitoring
    page can read it after any navigation or reload.
    """
    payload = {key: state.get(key) for key in MONITORING_KEYS if key in state}
    LAST_RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_FILE.write_text(json.dumps(payload, indent=2))
    return LAST_RUN_FILE


def load_last_run() -> dict | None:
    """
    Load the last persisted run snapshot (or None if nothing ran yet / the
    file got deleted). Fields missing from an old file simply come back as
    whatever `state.get()` returns in the caller.
    """
    if not LAST_RUN_FILE.exists():
        return None
    try:
        payload = json.loads(LAST_RUN_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    # Only restore something meaningful - a run needs at least timings or
    # token usage, otherwise the Monitoring page would still be empty.
    if not (payload.get("timings") or payload.get("token_usage")):
        return None
    return payload
