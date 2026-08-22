"""
LLM Judge Agent — scores every objection from the buyer agents for:
1. Groundedness: Is the trigger_line actually present on the page?
2. Real Buyer Realism: Would a real procurement exec raise this in a meeting?

Objections scoring < 6 on either dimension are flagged as WEAK or HALLUCINATED.
This directly answers the judge question: "How do we know the CFO is telling the truth?"
"""
import json
from typing import Any, Dict, List, Optional
from services.openrouter_client import call_openrouter, parse_json_response, DEFAULT_MODEL

_JUDGE_SYSTEM = """You are the Procurement Quality Judge — an independent auditor reviewing AI-generated buyer objections.

Your job is to evaluate each objection against the actual pricing page content for:

1. GROUNDED (0-10): Is the trigger_line actually present in the page content?
   - 9-10: Exact verbatim match or near-exact paraphrase
   - 6-8: Clearly implied by real content on the page
   - 3-5: Loosely related but not directly stated
   - 0-2: Cannot find this anywhere on the page (hallucinated)

2. REAL_BUYER (0-10): Would a real enterprise CFO/CISO/VP Eng raise this in a procurement meeting?
   - 9-10: Classic, well-documented procurement red flag
   - 6-8: Legitimate concern a real buyer would raise
   - 3-5: Theoretical, unlikely to block a real deal
   - 0-2: Invented concern, no real buyer raises this

VERDICT rules:
- grounded >= 6 AND real_buyer >= 6 → "VALID"
- grounded >= 6 AND real_buyer < 6  → "WEAK"
- grounded < 6                       → "HALLUCINATED"

Output ONLY a valid JSON array (no markdown, no extra text):
[
  {
    "objection_index": <int, 0-based>,
    "grounded_score": <int 0-10>,
    "real_buyer_score": <int 0-10>,
    "judge_verdict": "VALID" | "WEAK" | "HALLUCINATED",
    "judge_reasoning": "<one sentence explaining the verdict>"
  }
]"""


def run_judge_agent(
    objections: List[Dict[str, Any]],
    page_content: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> List[Dict[str, Any]]:
    """
    Scores all buyer-agent objections for groundedness and real-buyer realism.
    Returns the original objections list with judge scores merged in.
    """
    if not objections:
        return []

    # Build compact payload for the judge
    objections_summary = json.dumps(
        [
            {
                "index": i,
                "persona": obj.get("persona"),
                "trigger_line": obj.get("trigger_line"),
                "lethal_objection": obj.get("lethal_objection"),
            }
            for i, obj in enumerate(objections)
        ],
        indent=2,
    )

    messages = [
        {"role": "system", "content": _JUDGE_SYSTEM},
        {
            "role": "user",
            "content": (
                f"PRICING PAGE CONTENT (first 3000 chars):\n{page_content[:3000]}\n\n"
                f"OBJECTIONS TO JUDGE:\n{objections_summary}"
            ),
        },
    ]

    raw = call_openrouter(messages, model=model, api_key=api_key, temperature=0.1)
    scores = parse_json_response(raw)

    # Merge judge scores back into objections
    scored_map: Dict[int, Dict] = {s["objection_index"]: s for s in scores}
    result = []
    for i, obj in enumerate(objections):
        merged = dict(obj)
        score = scored_map.get(i, {})
        merged["judge_grounded_score"] = score.get("grounded_score", 5)
        merged["judge_real_buyer_score"] = score.get("real_buyer_score", 5)
        merged["judge_verdict"] = score.get("judge_verdict", "WEAK")
        merged["judge_reasoning"] = score.get("judge_reasoning", "Not evaluated.")
        result.append(merged)

    return result
