"""OpenAI-compatible JSON client for longform planning."""

from __future__ import annotations

import json
from typing import Any


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


class OpenAICompatibleJsonClient:
    """Small wrapper around the repo's OpenAI-compatible LLM endpoint."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        try:
            from config import API_BASE_URL, API_KEY, LLM_MODEL
        except Exception:
            API_BASE_URL = ""
            API_KEY = ""
            LLM_MODEL = ""
        self.api_key = api_key or API_KEY
        self.base_url = base_url or API_BASE_URL
        self.model = model or LLM_MODEL

    def complete_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        import requests

        endpoint = self.base_url.rstrip("/") + "/chat/completions"
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": messages,
                "temperature": 0.45,
                "response_format": {"type": "json_object"},
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        content = choices[0].get("message", {}).get("content", "{}") if choices else "{}"
        return _extract_json_object(content)
