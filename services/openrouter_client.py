"""
Shared OpenRouter API client used by all buyer agents and the judge agent.
Handles auth, model fallback, and JSON parsing in one place.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

FALLBACK_FREE_MODELS: List[str] = [
    "nvidia/nemotron-3.5-lightning:free",
    "dots-studio/dots-3-note-preview:free",
    "liquid/lfm-2.5-2.6b:free",
]

DEFAULT_MODEL = "nvidia/nemotron-3.5-lightning:free"


def _load_api_key(api_key: Optional[str] = None) -> str:
    if api_key:
        return api_key
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "OPENROUTER_API_KEY":
                        key = v.strip()
                        break
    if not key:
        raise ValueError("OPENROUTER_API_KEY not found. Set it in .env or as an environment variable.")
    return key


def call_openrouter(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    timeout: float = 45.0,
    temperature: float = 0.2,
) -> str:
    """
    Makes a single OpenRouter API call with automatic model fallback.
    Returns the raw text content from the LLM response.
    Raises RuntimeError if all fallback models fail.
    """
    key = _load_api_key(api_key)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "The Adversarial Buyer",
    }

    models_to_try = [model] + [m for m in FALLBACK_FREE_MODELS if m != model]
    last_err = None

    for candidate_model in models_to_try:
        payload = {
            "model": candidate_model,
            "messages": messages,
            "temperature": temperature,
        }
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)

            if response.status_code == 200:
                raw = response.json()["choices"][0]["message"]["content"].strip()
                return raw
            else:
                last_err = f"Model {candidate_model} → HTTP {response.status_code}: {response.text[:120]}"

        except Exception as e:
            last_err = f"Model {candidate_model} → {e}"
            continue

    raise RuntimeError(f"All OpenRouter models failed. Last error: {last_err}")


def parse_json_response(raw: str) -> Any:
    """
    Strips markdown code fences and parses JSON from an LLM response.
    """
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())
