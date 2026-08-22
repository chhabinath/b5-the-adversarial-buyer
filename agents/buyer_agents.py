"""
Three focused adversarial buyer agents — CFO, CISO, VP Engineering.
Each makes one targeted LLM call with a single-persona prompt.
Returns a list of objection dicts for the judge to score.
"""
from typing import Any, Dict, List, Optional
from services.openrouter_client import call_openrouter, parse_json_response, DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Shared objection schema note (for prompts)
# ---------------------------------------------------------------------------
_OBJECTION_SCHEMA = """
Output ONLY a valid JSON array (no markdown, no extra text):
[
  {
    "persona": "<role name>",
    "domain": "<domain>",
    "severity_score": <int 0-100>,
    "trigger_line": "<exact verbatim phrase from the pricing page causing this objection>",
    "lethal_objection": "<the ruthless buyer objection in one or two sentences>",
    "gtm_vulnerability": "<why the sales/GTM team cannot defend this in a procurement meeting>",
    "gtm_survival_fix": "<exact change required to the pricing page or positioning to survive>"
  }
]
Rules:
- trigger_line MUST be a verbatim or near-verbatim quote from the page content.
- Output 1-2 objections maximum. Be surgical, not exhaustive.
- Output ONLY a JSON array. No markdown. No extra text.
"""


# ---------------------------------------------------------------------------
# CFO Agent — Finance & Procurement
# ---------------------------------------------------------------------------
_CFO_SYSTEM = f"""You are the CFO of a 2,000-person enterprise company.
You are evaluating this vendor's pricing page as a hostile, skeptical procurement buyer.
Your attack vectors: hidden minimums, lock-in clauses, opaque unit costs, undisclosed overages,
no ROI benchmarks, and annual commitment traps.
You kill deals that carry budget uncertainty or undisclosed cost escalation risk.

{_OBJECTION_SCHEMA}"""


def run_cfo_agent(
    page_content: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> List[Dict[str, Any]]:
    """Run the CFO adversarial buyer agent. Returns list of objections."""
    messages = [
        {"role": "system", "content": _CFO_SYSTEM},
        {"role": "user", "content": f"Pricing page content:\n\n{page_content[:4000]}"},
    ]
    raw = call_openrouter(messages, model=model, api_key=api_key)
    objections = parse_json_response(raw)
    if not isinstance(objections, list):
        objections = [objections]
    for obj in objections:
        obj.setdefault("persona", "Chief Financial Officer (CFO)")
        obj.setdefault("domain", "Finance & Procurement")
        obj["agent"] = "cfo"
    return objections


# ---------------------------------------------------------------------------
# CISO Agent — Security & Compliance
# ---------------------------------------------------------------------------
_CISO_SYSTEM = f"""You are the CISO of a publicly-listed financial services company.
You are auditing this vendor's pricing page before approving any procurement.
Your attack vectors: SSO gated to expensive tiers, vague SOC 2 / ISO 27001 claims,
no data residency options, audit logs paywalled, GDPR ambiguity, and no pen-test evidence.
Any security feature monetized as an upsell is an immediate vendor disqualification.

{_OBJECTION_SCHEMA}"""


def run_ciso_agent(
    page_content: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> List[Dict[str, Any]]:
    """Run the CISO adversarial buyer agent. Returns list of objections."""
    messages = [
        {"role": "system", "content": _CISO_SYSTEM},
        {"role": "user", "content": f"Pricing page content:\n\n{page_content[:4000]}"},
    ]
    raw = call_openrouter(messages, model=model, api_key=api_key)
    objections = parse_json_response(raw)
    if not isinstance(objections, list):
        objections = [objections]
    for obj in objections:
        obj.setdefault("persona", "Chief Information Security Officer (CISO)")
        obj.setdefault("domain", "Security & Compliance")
        obj["agent"] = "ciso"
    return objections


# ---------------------------------------------------------------------------
# VP Engineering Agent — Technical & SLA
# ---------------------------------------------------------------------------
_VPENG_SYSTEM = f"""You are the VP of Engineering at a Series C startup scaling to enterprise.
You are reviewing this vendor's pricing page before approving a production dependency.
Your attack vectors: vague "fair use" API throttle policies, missing SLA uptime numbers,
no explicit rate limits, no status page, ambiguous support tier SLAs, no sandbox/staging environment,
and per-seat pricing that breaks at scale.
You kill deals where the vendor cannot guarantee production reliability under contract.

{_OBJECTION_SCHEMA}"""


def run_vpeng_agent(
    page_content: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> List[Dict[str, Any]]:
    """Run the VP Engineering adversarial buyer agent. Returns list of objections."""
    messages = [
        {"role": "system", "content": _VPENG_SYSTEM},
        {"role": "user", "content": f"Pricing page content:\n\n{page_content[:4000]}"},
    ]
    raw = call_openrouter(messages, model=model, api_key=api_key)
    objections = parse_json_response(raw)
    if not isinstance(objections, list):
        objections = [objections]
    for obj in objections:
        obj.setdefault("persona", "VP of Engineering")
        obj.setdefault("domain", "Technical & SLA")
        obj["agent"] = "vpeng"
    return objections
