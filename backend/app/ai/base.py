from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class ChatTurn:
    role: str  # system | user | assistant
    content: str


class AIProvider(abc.ABC):
    """Common interface implemented by every AI backend."""

    name: str
    model: str

    @abc.abstractmethod
    async def complete_json(self, system: str, user: str) -> str:
        """Return a raw model response expected to contain JSON."""

    @abc.abstractmethod
    async def chat(self, turns: list[ChatTurn]) -> str:
        """Return a free-text assistant reply for a conversation."""


class AIProviderError(Exception):
    """Raised when the underlying provider is unreachable or errors out."""
