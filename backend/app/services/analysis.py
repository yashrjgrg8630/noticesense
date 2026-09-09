from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime

from app.ai.base import AIProvider
from app.ai.prompts import (
    ANALYSIS_SYSTEM,
    build_analysis_user_prompt,
)

_VALID_CATEGORIES = {
    "tax", "legal", "utility", "banking", "insurance", "education",
    "immigration", "healthcare", "employment", "other",
}
_VALID_URGENCY = {"high", "medium", "low"}


@dataclass
class ParsedDeadline:
    label: str
    due_date: date | None
    raw_text: str | None
    source_page: int | None


@dataclass
class ParsedAction:
    description: str
    due_date: date | None
    source_page: int | None


@dataclass
class AnalysisResult:
    title: str | None = None
    issuer: str | None = None
    category: str | None = None
    urgency: str | None = None
    reference_number: str | None = None
    summary: str | None = None
    deadlines: list[ParsedDeadline] = field(default_factory=list)
    actions: list[ParsedAction] = field(default_factory=list)


def _parse_date(value) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _extract_json(raw: str) -> dict:
    """Pull the first JSON object out of a model response."""
    raw = raw.strip()
    # Strip common markdown code fences.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model response.")
    return json.loads(raw[start : end + 1])


def _clean_str(value) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or None


def parse_analysis(raw: str) -> AnalysisResult:
    data = _extract_json(raw)

    category = _clean_str(data.get("category"))
    if category:
        category = category.lower()
        if category not in _VALID_CATEGORIES:
            category = "other"

    urgency = _clean_str(data.get("urgency"))
    if urgency:
        urgency = urgency.lower()
        if urgency not in _VALID_URGENCY:
            urgency = None

    deadlines: list[ParsedDeadline] = []
    for item in data.get("deadlines") or []:
        if not isinstance(item, dict):
            continue
        label = _clean_str(item.get("label"))
        if not label:
            continue
        deadlines.append(
            ParsedDeadline(
                label=label,
                due_date=_parse_date(item.get("due_date")),
                raw_text=_clean_str(item.get("raw_text")),
                source_page=item.get("source_page") if isinstance(item.get("source_page"), int) else None,
            )
        )

    actions: list[ParsedAction] = []
    for item in data.get("actions") or []:
        if not isinstance(item, dict):
            continue
        description = _clean_str(item.get("description"))
        if not description:
            continue
        actions.append(
            ParsedAction(
                description=description,
                due_date=_parse_date(item.get("due_date")),
                source_page=item.get("source_page") if isinstance(item.get("source_page"), int) else None,
            )
        )

    return AnalysisResult(
        title=_clean_str(data.get("title")),
        issuer=_clean_str(data.get("issuer")),
        category=category,
        urgency=urgency,
        reference_number=_clean_str(data.get("reference_number")),
        summary=_clean_str(data.get("summary")),
        deadlines=deadlines,
        actions=actions,
    )


async def analyze_pages(provider: AIProvider, pages: list[tuple[int, str]]) -> AnalysisResult:
    user_prompt = build_analysis_user_prompt(pages)
    raw = await provider.complete_json(ANALYSIS_SYSTEM, user_prompt)
    return parse_analysis(raw)
