"""
agents.py – NoticeSense Phase 3
Three-agent architecture powered by Google Gemini API (google-genai SDK).

Agents:
  - IntentAgent    : Identifies notice type & generates a summary.
  - DeadlineAgent  : Extracts deadlines, effective dates & days remaining.
  - ActionAgent    : Converts notice into ordered actionable steps.

Guardrails (applied to every agent):
  - Never hallucinate information not in the notice text.
  - If a field is missing, clearly state it is not mentioned.
  - Do NOT provide legal advice.
  - Keep responses short and factual.

API Key is loaded from .env via backend/core/config.py (GEMINI_API_KEY).
"""

import re
import time
from google import genai
from google.genai import types
from backend.core.config import settings

# ── Shared guardrail suffix appended to every agent prompt ──────────────────
_GUARDRAILS = """
---
GUARDRAILS (follow strictly):
- Only use information explicitly present in the notice text below.
- NEVER invent, assume, or extrapolate deadlines, dates, or names.
- Do NOT provide legal advice of any kind.
- If the requested information is not in the notice, say so clearly.
- Keep your response concise and factual.
"""

_MODEL = "gemini-1.5-flash"


def _make_client() -> genai.Client:
    """Creates a Gemini client using the API key from .env via config."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _generate(system_prompt: str, user_prompt: str, retries: int = 3) -> str:
    """
    Routes to Gemini or Ollama based on LLM_BACKEND setting in .env.
    Retries on transient 429 errors (Gemini only).
    """
    backend = settings.LLM_BACKEND.lower()

    if backend == "ollama":
        return _generate_ollama(system_prompt, user_prompt)
    else:
        return _generate_gemini(system_prompt, user_prompt, retries)


def _generate_gemini(system_prompt: str, user_prompt: str, retries: int = 3) -> str:
    """Calls Gemini 1.5 Flash with retry/backoff on 429."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                    max_output_tokens=1024,
                ),
            )
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            raise


def _generate_ollama(system_prompt: str, user_prompt: str) -> str:
    """Calls a local model via Ollama using chat messages."""
    import ollama
    response = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    return response["message"]["content"].strip()


# ===========================================================================
# 1. IntentAgent
# ===========================================================================
class IntentAgent:
    """
    Identifies the type and purpose of an official notice and
    generates a concise plain-language summary.
    """

    SYSTEM_PROMPT = (
        """You are IntentAgent, an AI assistant specialised in analysing
official government and corporate notices. Your job is to:

1. Identify the NOTICE TYPE from this list (pick the best match):
   Legal Notice | Compliance Notice | Tax Notice | Regulatory Circular |
   Court Notice | Academic Notice | Banking Circular | General Notice | Unknown

2. Write a SHORT SUMMARY (3-5 sentences max) explaining:
   - What this notice is about
   - Who issued it
   - Who it is addressed to / affects
   - The core message or instruction

Format your response EXACTLY as:
NOTICE TYPE: <type>
SUMMARY: <summary>
"""
        + _GUARDRAILS
    )

    def analyze(self, notice_text: str) -> dict:
        prompt = f"NOTICE TEXT:\n\"\"\"\n{notice_text}\n\"\"\""
        try:
            raw = _generate(self.SYSTEM_PROMPT, prompt)
            notice_type, summary = "Unknown", raw
            for line in raw.splitlines():
                if line.upper().startswith("NOTICE TYPE:"):
                    notice_type = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SUMMARY:"):
                    rest_idx = raw.find(line) + len(line)
                    summary = line.split(":", 1)[1].strip()
                    remainder = raw[rest_idx:].strip()
                    if remainder:
                        summary = summary + " " + remainder
            return {"notice_type": notice_type, "summary": summary, "raw_response": raw}
        except Exception as e:
            return {"notice_type": "Error", "summary": f"IntentAgent failed: {e}", "raw_response": ""}


# ===========================================================================
# 2. DeadlineAgent
# ===========================================================================
class DeadlineAgent:
    """
    Extracts all time-sensitive dates from the notice.
    """

    SYSTEM_PROMPT = (
        """You are DeadlineAgent, an AI assistant specialised in extracting
time-sensitive information from official notices. Your job is to:

1. Find ALL deadlines, compliance dates, and effective dates in the notice.
2. For each date found, state:
   - Date label (e.g., "Compliance Deadline", "Effective Date", "Submission By")
   - The exact date as written in the notice
3. If NO dates are mentioned, respond with EXACTLY:
   No deadline mentioned in the notice

Format your response as a numbered list:
1. <Label>: <Date as written in notice>
2. <Label>: <Date as written in notice>

Or if none found:
No deadline mentioned in the notice
"""
        + _GUARDRAILS
    )

    def analyze(self, notice_text: str) -> dict:
        prompt = f"NOTICE TEXT:\n\"\"\"\n{notice_text}\n\"\"\""
        try:
            raw = _generate(self.SYSTEM_PROMPT, prompt)
            has_deadline = "no deadline mentioned" not in raw.lower()
            deadlines = []
            if has_deadline:
                for match in re.finditer(r"^\d+\.\s*(.+?):\s*(.+)$", raw, re.MULTILINE):
                    deadlines.append({"label": match.group(1).strip(), "date": match.group(2).strip()})
                if not deadlines:
                    deadlines.append({"label": "Deadline", "date": raw})
            return {
                "has_deadline": has_deadline,
                "deadlines": deadlines,
                "no_deadline_message": "No deadline mentioned in the notice" if not has_deadline else None,
                "raw_response": raw,
            }
        except Exception as e:
            return {"has_deadline": False, "deadlines": [], "no_deadline_message": f"DeadlineAgent failed: {e}", "raw_response": ""}


# ===========================================================================
# 3. ActionAgent
# ===========================================================================
class ActionAgent:
    """
    Converts the notice into a clear, ordered list of actions.
    """

    SYSTEM_PROMPT = (
        """You are ActionAgent, an AI assistant specialised in converting
official notices into clear, actionable guidance. Your job is to:

1. Read the notice carefully.
2. Extract the specific actions the RECIPIENT must take.
3. Present them as a numbered list, ordered by priority/urgency.
4. Each action must be specific, concrete, and in plain language.

Format your response EXACTLY as:
1. <Action>
2. <Action>
...

If no clear actions can be identified, state:
No specific actions could be identified from the notice.
"""
        + _GUARDRAILS
    )

    def analyze(self, notice_text: str) -> dict:
        prompt = f"NOTICE TEXT:\n\"\"\"\n{notice_text}\n\"\"\""
        try:
            raw = _generate(self.SYSTEM_PROMPT, prompt)
            actions = [m.group(1).strip() for m in re.finditer(r"^\d+\.\s*(.+)$", raw, re.MULTILINE) if m.group(1).strip()]
            if not actions:
                actions = [raw] if raw else ["No specific actions could be identified from the notice."]
            return {"actions": actions, "raw_response": raw}
        except Exception as e:
            return {"actions": [f"ActionAgent failed: {e}"], "raw_response": ""}
