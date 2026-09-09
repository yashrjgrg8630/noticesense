from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIProviderError, ChatTurn
from app.core.config import settings

_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.model = settings.ollama_model
        self.base_url = settings.ollama_base_url.rstrip("/")

    async def _post_chat(self, messages: list[dict], fmt: str | None = None) -> str:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1},
        }
        if fmt == "json":
            payload["format"] = "json"
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise AIProviderError(
                f"Ollama request failed ({exc}). Is Ollama running and the model '{self.model}' pulled?"
            ) from exc
        return (data.get("message") or {}).get("content", "").strip()

    async def complete_json(self, system: str, user: str) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return await self._post_chat(messages, fmt="json")

    async def chat(self, turns: list[ChatTurn]) -> str:
        messages = [{"role": t.role, "content": t.content} for t in turns]
        return await self._post_chat(messages)
