"""
chat.py – NoticeSense Phase 3
Professional chat interface with session-based memory.
"""

import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from backend.core.config import settings
from frontend.styles import inject_global_css, page_header

_SYSTEM_INSTRUCTION = """You are NoticeSense Assistant — a precise AI that answers
questions about an official notice document.

Rules:
- Answer ONLY based on the notice text provided in the conversation context.
- Do NOT invent or assume information not in the notice.
- Do NOT give legal advice. Guide the user to seek professional legal counsel.
- Be concise, clear, and friendly.
- If you are unsure, say so honestly.
"""


def _chat_reply(notice_text: str, chat_history: list, user_message: str) -> str:
    """Routes to Ollama or Gemini based on LLM_BACKEND setting."""
    backend = settings.LLM_BACKEND.lower()

    messages = [
        {"role": "system", "content": _SYSTEM_INSTRUCTION},
        {"role": "user", "content": (
            f"Official notice text:\n---\n{notice_text}\n---\n"
            f"Use only this to answer questions."
        )},
        {"role": "assistant", "content": "Understood. I'll answer based on the notice."},
    ]
    for msg in chat_history[:-1]:
        messages.append({
            "role": msg["role"] if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": user_message})

    if backend == "ollama":
        import ollama
        response = ollama.chat(model=settings.OLLAMA_MODEL, messages=messages)
        return response["message"]["content"].strip()
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        contents = []
        for m in messages[1:]:  # skip system (handled via system_instruction)
            role = "user" if m["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                temperature=0.3,
                max_output_tokens=512,
            ),
        )
        return response.text.strip()


def show_chat():
    inject_global_css()
    page_header("💬", "Chat with Your Notice",
                "Ask anything — the AI answers based only on the uploaded notice.")

    st.markdown("""
    <style>
    /* Tighter chat layout */
    [data-testid="stChatInputContainer"] textarea {
        background: #111827 !important;
        border: 1px solid rgba(124,106,247,0.35) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-size: 14px !important;
    }
    [data-testid="stChatMessage"][data-testid*="user"] {
        border-left: 3px solid #7c6af7 !important;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        border-left: 3px solid #22c55e !important;
    }
    </style>
    """, unsafe_allow_html=True)

    notice_text = st.session_state.get("cleaned_text", "")
    if not notice_text:
        st.markdown("""
        <div style="text-align:center;padding:56px 0">
            <div style="font-size:44px">💬</div>
            <div style="font-size:15px;font-weight:600;color:#64748b;margin-top:12px">
                No notice loaded
            </div>
            <div style="font-size:13px;color:#334155;margin-top:6px">
                Upload and analyse a notice from the Home page first.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Suggested prompts ─────────────────────────────────────────────────────
    if not st.session_state.get("chat_history"):
        st.markdown("""
        <div style="font-size:11px;font-weight:600;letter-spacing:.8px;color:#475569;margin-bottom:10px">
            SUGGESTED QUESTIONS
        </div>
        """, unsafe_allow_html=True)

        suggestions = [
            "What is the main purpose of this notice?",
            "What are the key deadlines?",
            "What actions should I take?",
        ]
        cols = st.columns(3)
        for col, s in zip(cols, suggestions):
            if col.button(s, use_container_width=True):
                st.session_state.setdefault("chat_history", [])
                st.session_state.chat_history.append({"role": "user", "content": s})
                with st.spinner("Thinking…"):
                    try:
                        reply = _chat_reply(notice_text, st.session_state.chat_history, s)
                    except Exception as e:
                        reply = f"⚠️ {str(e)}"
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

        st.markdown("<hr class='ns-divider'>", unsafe_allow_html=True)

    # ── Chat history ──────────────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ── Input ─────────────────────────────────────────────────────────────────
    user_input = st.chat_input("Type your question about the notice…")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    reply = _chat_reply(notice_text, st.session_state.chat_history, user_input)
                except Exception as e:
                    reply = f"⚠️ Error: {str(e)}"
            st.write(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # ── Sidebar reset ─────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("<hr style='border-color:rgba(255,255,255,0.07)'>", unsafe_allow_html=True)
        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state.pop("chat_history", None)
            st.rerun()
