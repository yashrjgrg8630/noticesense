from __future__ import annotations

import re

from app.ai.base import AIProvider, ChatTurn
from app.ai.prompts import CHAT_SYSTEM, build_chat_context

# Assistant answers cite pages inline as [p2]. We parse those markers into
# structured citations, quoting a snippet from the referenced page.
_CITATION_RE = re.compile(r"\[p(\d+)\]", re.IGNORECASE)
_MAX_HISTORY_TURNS = 12


def extract_citations(answer: str, page_texts: dict[int, str]) -> list[dict]:
    citations: list[dict] = []
    seen: set[int] = set()
    for match in _CITATION_RE.finditer(answer):
        page_number = int(match.group(1))
        if page_number in seen:
            continue
        text = page_texts.get(page_number)
        if not text:
            continue
        seen.add(page_number)
        snippet = " ".join(text.split())[:280]
        citations.append({"page_number": page_number, "quote": snippet})
    return citations


async def answer_question(
    provider: AIProvider,
    pages: list[tuple[int, str]],
    history: list[tuple[str, str]],
    question: str,
) -> tuple[str, list[dict]]:
    """Return (answer, citations)."""
    turns: list[ChatTurn] = [
        ChatTurn(role="system", content=CHAT_SYSTEM),
        ChatTurn(role="system", content=build_chat_context(pages)),
    ]
    for role, content in history[-_MAX_HISTORY_TURNS:]:
        turns.append(ChatTurn(role=role, content=content))
    turns.append(ChatTurn(role="user", content=question))

    answer = await provider.chat(turns)
    page_texts = {number: text for number, text in pages}
    citations = extract_citations(answer, page_texts)
    return answer, citations
