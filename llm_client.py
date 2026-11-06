"""
Pluggable text-generation backend.

Three engines, selected by config["content_engine"] (or env var CONTENT_ENGINE):

  "template"  -> returns None immediately. Callers fall back to the
                 hand-written templates in prompts/templates.py.
                 Zero cost, zero setup, works with no internet at all
                 once dependencies are installed. THIS IS THE DEFAULT.

  "ollama"    -> calls a locally-running Ollama server (https://ollama.com).
                 Free and runs on your own machine / GitHub Actions runner.
                 No API key. Slower and lower quality than a hosted frontier
                 model, but genuinely free.

  "anthropic" -> calls the real Claude API. Best quality, but this is a
                 PAID service billed by Anthropic — only used if you
                 explicitly set CONTENT_ENGINE=anthropic and provide
                 ANTHROPIC_API_KEY. Never enabled by default.

Every call function returns a plain string (the model's raw text) or None
on failure, so callers can always fall back to templates and a scheduled
run never crashes just because an optional LLM backend is unavailable.
"""

import json
import os

import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-6"


def get_completion(prompt: str, system: str = None, max_tokens: int = 1200, cfg: dict = None) -> str | None:
    """Dispatch to the configured engine. Returns text or None."""
    engine = (cfg or {}).get("content_engine", "template")

    if engine == "anthropic":
        return _call_anthropic(prompt, system, max_tokens)
    if engine == "ollama":
        return _call_ollama(prompt, system, cfg)

    return None  # "template" engine — caller uses prompts/templates.py


def _call_anthropic(prompt, system, max_tokens):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[llm_client] CONTENT_ENGINE=anthropic but ANTHROPIC_API_KEY is not set — falling back to templates.")
        return None
    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system or "",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(parts).strip() or None
    except Exception as e:  # noqa: BLE001 — a failed LLM call should never crash the pipeline
        print(f"[llm_client] Anthropic call failed, falling back to templates: {e}")
        return None


def _call_ollama(prompt, system, cfg):
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    try:
        resp = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": full_prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip() or None
    except Exception as e:  # noqa: BLE001
        print(f"[llm_client] Ollama call failed (is `ollama serve` running? model pulled?), falling back to templates: {e}")
        return None


def parse_json_safely(text: str):
    """Best-effort JSON extraction from an LLM response (strips ```json fences etc.)."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return None
        return None
