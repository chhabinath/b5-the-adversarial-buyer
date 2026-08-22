import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

FALLBACK_FREE_MODELS: List[str] = [
    "nvidia/nemotron-3.5-lightning:free",
    "dots-studio/dots-3-note-preview:free",
    "liquid/lfm-2.5-2.6b:free",
]

DEFAULT_MODEL = "nvidia/nemotron-3.5-lightning:free"

SYSTEM_PROMPT = """You are "The Adversarial Buyer" — the most ruthless, skeptical enterprise procurement committee in the world.
Your sole mission: inspect the company's pricing page, find its weakest commercial assumptions, and KILL THE DEAL.

You represent a hostile buying committee featuring:
1. The Skeptical CFO (Attacking lock-in, hidden minimums, opaque ROI, unbudgeted risks)
2. The Paranoid CISO (Attacking gated SSO, vague SOC2/data residency, security upselling)
3. The Battle-Hardened VP of Engineering (Attacking SLA vagueness, API throttles, fair-use traps)

You MUST identify the top 3-5 lethal objections that the company's Go-To-Market (GTM) team cannot currently survive.
Rank them strictly in descending order of damage (highest severity first).

You MUST output ONLY a valid JSON object matching this schema:
{
  "deal_verdict": "DEAL REJECTED" | "DEAL AT RISK" | "SURVIVED WITH WARNINGS",
  "overall_damage_score": <int 0-100>,
  "deal_killer_headline": "<one sharp sentence summarizing why the deal dies>",
  "ranked_objections": [
    {
      "rank": 1,
      "rank_badge": "LETHAL DEAL KILLER",
      "persona": "Chief Financial Officer (CFO)",
      "domain": "Finance & Procurement",
      "severity_score": <int 0-100>,
      "trigger_line": "<exact verbatim quote from the page causing this objection>",
      "gtm_vulnerability": "<why the sales team/GTM cannot defend this against procurement>",
      "lethal_objection": "<the ruthless, skeptical buyer objection>",
      "gtm_survival_fix": "<exact positioning, pricing, or page change required to survive>"
    }
  ]
}

Rules:
- Quote the EXACT line/phrase from the site behind each objection.
- Ensure objections are sorted from highest severity_score to lowest.
- Output ONLY valid raw JSON without markdown codeblocks or extra text.
"""


def analyze_pricing(
    content: str,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Analyzes scraped pricing markdown content using OpenRouter via pure httpx.
    Generates a ranked list of deal-killing objections with verbatim page line citations.
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY not found in environment or .env file.")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "The Adversarial Buyer",
    }

    truncated_content = content[:5000]
    models_to_try = [model] + [m for m in FALLBACK_FREE_MODELS if m != model]
    last_err = None

    for candidate_model in models_to_try:
        payload = {
            "model": candidate_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Target Company Pricing & Site Content:\n\n{truncated_content}"},
            ],
            "temperature": 0.2,
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)

            if response.status_code == 200:
                raw_response = response.json()["choices"][0]["message"]["content"].strip()

                if raw_response.startswith("```json"):
                    raw_response = raw_response[7:]
                if raw_response.startswith("```"):
                    raw_response = raw_response[3:]
                if raw_response.endswith("```"):
                    raw_response = raw_response[:-3]

                parsed = json.loads(raw_response.strip())
                # Ensure objections are strictly sorted by severity score descending
                if "ranked_objections" in parsed and isinstance(parsed["ranked_objections"], list):
                    parsed["ranked_objections"].sort(
                        key=lambda x: x.get("severity_score", 0), reverse=True
                    )
                    for idx, obj in enumerate(parsed["ranked_objections"], start=1):
                        obj["rank"] = idx
                        if idx == 1:
                            obj["rank_badge"] = "LETHAL DEAL KILLER"
                        elif idx == 2:
                            obj["rank_badge"] = "CRITICAL BLOCKER"
                        else:
                            obj["rank_badge"] = "PROCUREMENT GATE"
                return parsed
            else:
                last_err = f"Model {candidate_model} returned HTTP {response.status_code}: {response.text[:120]}"
        except Exception as e:
            last_err = f"Model {candidate_model} failed: {e}"
            continue

    raise RuntimeError(f"All free OpenRouter models failed. Last error: {last_err}")
