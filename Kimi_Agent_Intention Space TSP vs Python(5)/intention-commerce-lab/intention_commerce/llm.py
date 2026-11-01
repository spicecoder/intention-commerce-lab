"""Optional LLM policies. The deterministic policy is the default for tests."""
from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib import error, request


class LLMError(RuntimeError):
    pass


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise LLMError("The LLM response did not contain a JSON object")
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"Invalid LLM JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise LLMError("The LLM policy response must be a JSON object")
    return value


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise LLMError(f"LLM HTTP {exc.code}: {detail}") from exc
    except (error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise LLMError(f"LLM request failed: {exc}") from exc


class OllamaClient:
    name = "ollama"

    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        response = post_json(f"{self.base_url}/api/chat", {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }, {}, self.timeout)
        try:
            return parse_json_object(response["message"]["content"])
        except KeyError as exc:
            raise LLMError("Ollama response lacked message.content") from exc


class ApiClient:
    """OpenAI-compatible chat-completions client, including Moonshot endpoints."""

    name = "api"

    def __init__(self) -> None:
        self.base_url = os.getenv("API_BASE_URL", "https://api.moonshot.ai/v1").rstrip("/")
        self.api_key = os.getenv("API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("API_MODEL", "")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
        if not self.api_key:
            raise LLMError("Set API_KEY (or MOONSHOT_API_KEY / OPENAI_API_KEY) for --client api")
        if not self.model:
            raise LLMError("Set API_MODEL to the model identifier supplied by your API provider")

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        response = post_json(f"{self.base_url}/chat/completions", {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }, {"Authorization": f"Bearer {self.api_key}"}, self.timeout)
        try:
            return parse_json_object(response["choices"][0]["message"]["content"])
        except (KeyError, IndexError) as exc:
            raise LLMError("API response lacked choices[0].message.content") from exc


def make_llm_client(name: str) -> OllamaClient | ApiClient:
    if name == "ollama":
        return OllamaClient()
    if name == "api":
        return ApiClient()
    raise ValueError(f"Unsupported LLM client: {name}")
