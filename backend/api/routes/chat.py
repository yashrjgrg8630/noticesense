"""
routes/chat.py – POST /api/chat
Session-aware chat endpoint using the same LLM backend as agents (Ollama/Gemini).
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.config import settings
from backend.api.routes.upload import get_session

router = APIRouter()

_SYSTEM = """You are NoticeSense Assistant — a precise AI that answers
questions about an official notice document.
- Answer ONLY based on the notice text provided.
- Do NOT invent information not in the notice.
- Do NOT give legal advice.
- Be concise, clear, and friendly.
- If unsure, say so honestly."""


class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: list[dict] = []   # [{"role":"user"|"assistant","content":"..."}]


@router.post("/chat")
async def chat(req: ChatRequest):
    session = get_session(req.session_id)
    notice_text = session["cleaned_text"]

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"Official notice text:\n---\n{notice_text}\n---\n"
            "Use only this to answer questions."
        )},
        {"role": "assistant", "content": "Understood. I'll answer based on the notice."},
    ]
    for h in req.history:
        messages.append({
            "role": h["role"] if h["role"] == "user" else "assistant",
            "content": h["content"],
        })
    messages.append({"role": "user", "content": req.message})

    backend = settings.LLM_BACKEND.lower()

    if backend == "ollama":
        import ollama
        response = ollama.chat(model=settings.OLLAMA_MODEL, messages=messages)
        reply = response["message"]["content"].strip()
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])]
            )
            for m in messages[1:]   # skip system (sent via system_instruction)
        ]
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM,
                temperature=0.3,
                max_output_tokens=512,
            ),
        )
        reply = resp.text.strip()

    return {"reply": reply}
