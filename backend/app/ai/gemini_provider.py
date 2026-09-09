from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIProviderError, ChatTurn
from app.core.config import settings

_TIMEOUT = httpx.Timeout(120.0, connect=10.0)
_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise AIProviderError(
                "AI_PROVIDER is 'gemini' but GEMINI_API_KEY is not set."
            )
        self.model = settings.gemini_model
        self.api_key = settings.gemini_api_key

    async def _generate(self, system: str, contents: list[dict], json_mode: bool) -> str:
        generation_config: dict = {"temperature": 0.1}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": generation_config,
        }
        url = f"{_BASE}/models/{self.model}:generateContent?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Gemini request failed ({exc}).") from exc

        candidates = data.get("candidates") or []
        if not candidates:
            raise AIProviderError("Gemini returned no candidates.")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        return "".join(part.get("text", "") for part in parts).strip()

    async def complete_json(self, system: str, user: str) -> str:
        contents = [{"role": "user", "parts": [{"text": user}]}]
        return await self._generate(system, contents, json_mode=True)

    async def chat(self, turns: list[ChatTurn]) -> str:
        system_parts = [t.content for t in turns if t.role == "system"]
        system = "\n\n".join(system_parts)
        contents = []
        for turn in turns:
            if turn.role == "system":
                continue
            role = "model" if turn.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": turn.content}]})
        return await self._generate(system, contents, json_mode=False)
