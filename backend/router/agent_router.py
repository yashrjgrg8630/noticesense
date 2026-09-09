"""
agent_router.py – NoticeSense Phase 3
Orchestrates the three-agent pipeline: Intent → Deadline → Action.
Returns a unified result dict used by the Dashboard UI.
"""

from datetime import date, datetime
from backend.agents import IntentAgent, DeadlineAgent, ActionAgent


def _calculate_days_remaining(date_str: str) -> int | None:
    """
    Parses a date string (in many formats) and returns days remaining from today.
    Strips ordinal suffixes like 1st, 2nd, 3rd, 15th before parsing.
    Returns None if the date cannot be parsed.
    """
    import re as _re

    # Strip ordinal suffixes: 1st → 1, 2nd → 2, 15th → 15
    cleaned = _re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", date_str.strip(), flags=_re.IGNORECASE)
    # Normalise multiple spaces
    cleaned = " ".join(cleaned.split())

    formats = [
        "%d %B %Y",      # 15 March 2024
        "%d %B, %Y",     # 15 March, 2024
        "%B %d, %Y",     # March 15, 2024
        "%B %d %Y",      # March 15 2024
        "%d/%m/%Y",      # 15/03/2024
        "%m/%d/%Y",      # 03/15/2024
        "%d-%m-%Y",      # 15-03-2024
        "%Y-%m-%d",      # 2024-03-15
        "%d.%m.%Y",      # 15.03.2024
        "%d %b %Y",      # 15 Mar 2024
        "%d %b, %Y",     # 15 Mar, 2024
        "%b %d, %Y",     # Mar 15, 2024
        "%b %d %Y",      # Mar 15 2024
        "%B %Y",         # March 2024  (no day → treat as 1st of month)
        "%b %Y",         # Mar 2024
        "%d/%m/%y",      # 15/03/24
        "%d-%m-%y",      # 15-03-24
    ]

    today = date.today()
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            return (parsed - today).days
        except ValueError:
            continue
    return None



def run_agents(cleaned_text: str) -> dict:
    """
    Master orchestrator – runs all three agents on the cleaned notice text.

    Args:
        cleaned_text (str): Cleaned OCR text produced by Phase 2 pipeline.

    Returns:
        dict with keys:
            intent   – IntentAgent output
            deadline – DeadlineAgent output (with days_remaining injected)
            action   – ActionAgent output
            error    – None or error string
    """
    result = {
        "intent": None,
        "deadline": None,
        "action": None,
        "error": None,
    }

    try:
        # ── 1. Intent Agent ─────────────────────────────────────────────────
        intent_agent = IntentAgent()
        result["intent"] = intent_agent.analyze(cleaned_text)

        # ── 2. Deadline Agent ────────────────────────────────────────────────
        deadline_agent = DeadlineAgent()
        deadline_result = deadline_agent.analyze(cleaned_text)

        # Inject days_remaining for each deadline found
        if deadline_result.get("has_deadline") and deadline_result.get("deadlines"):
            for item in deadline_result["deadlines"]:
                days = _calculate_days_remaining(item["date"])
                item["days_remaining"] = days  # int or None

        result["deadline"] = deadline_result

        # ── 3. Action Agent ──────────────────────────────────────────────────
        action_agent = ActionAgent()
        result["action"] = action_agent.analyze(cleaned_text)

    except Exception as e:
        result["error"] = f"Agent pipeline failed: {str(e)}"

    return result
