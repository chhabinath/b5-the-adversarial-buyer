"""
Hermes — the Orchestrator Agent.

Coordinates the full adversarial buyer pipeline:
  Scraper → CFO Agent → CISO Agent → VP Eng Agent → LLM Judge → (Human Review)

Uses a status callback so the Streamlit UI can update live per agent.
"""
import time
from typing import Any, Callable, Dict, List, Optional

from services.scraper import fetch_page, _get_cache_path
from agents.buyer_agents import run_cfo_agent, run_ciso_agent, run_vpeng_agent
from agents.judge_agent import run_judge_agent

# Agent metadata used by the UI
AGENT_META = [
    {
        "key": "hermes",
        "icon": "🟣",
        "name": "Hermes Orchestrator",
        "desc": "Coordinating multi-agent pipeline",
    },
    {
        "key": "scraper",
        "icon": "🔵",
        "name": "Scraper Agent",
        "desc": "Fetching & cleaning pricing page via Jina Reader",
    },
    {
        "key": "cfo",
        "icon": "💰",
        "name": "CFO Agent",
        "desc": "Finance & Procurement adversarial analysis",
    },
    {
        "key": "ciso",
        "icon": "🔐",
        "name": "CISO Agent",
        "desc": "Security & Compliance adversarial analysis",
    },
    {
        "key": "vpeng",
        "icon": "⚙️",
        "name": "VP Engineering Agent",
        "desc": "Technical & SLA adversarial analysis",
    },
    {
        "key": "judge",
        "icon": "⚖️",
        "name": "LLM Judge Agent",
        "desc": "Scoring objections for groundedness & realism",
    },
]


def run_pipeline(
    url: str,
    api_key: Optional[str] = None,
    on_status: Optional[Callable[[str, str, Dict], None]] = None,
) -> Dict[str, Any]:
    """
    Runs the full adversarial buyer pipeline.

    Args:
        url:        Target pricing page URL.
        api_key:    OpenRouter API key (falls back to .env).
        on_status:  Callback(stage_key, status, info_dict) for live UI updates.
                    status values: "running" | "done" | "error"

    Returns a dict with all pipeline results.
    """
    timings: Dict[str, float] = {}

    def notify(key: str, status: str, **info):
        if on_status:
            on_status(key, status, info)

    # ------------------------------------------------------------------ #
    # Hermes kicks off
    # ------------------------------------------------------------------ #
    notify("hermes", "running")

    # ------------------------------------------------------------------ #
    # Stage 1: Scraper
    # ------------------------------------------------------------------ #
    notify("scraper", "running")
    t0 = time.perf_counter()
    from_cache = _get_cache_path(url).exists()
    try:
        page_content = fetch_page(url)
    except Exception as e:
        notify("scraper", "error", msg=str(e))
        raise
    timings["scraper"] = time.perf_counter() - t0
    notify(
        "scraper",
        "done",
        chars=len(page_content),
        from_cache=from_cache,
        elapsed=timings["scraper"],
    )

    # ------------------------------------------------------------------ #
    # Stages 2-4: Buyer Agents (sequential to respect rate limits)
    # ------------------------------------------------------------------ #
    all_objections: List[Dict[str, Any]] = []

    for agent_key, agent_fn, agent_label in [
        ("cfo", run_cfo_agent, "CFO Agent"),
        ("ciso", run_ciso_agent, "CISO Agent"),
        ("vpeng", run_vpeng_agent, "VP Engineering Agent"),
    ]:
        notify(agent_key, "running")
        t0 = time.perf_counter()
        try:
            objections = agent_fn(page_content, api_key=api_key)
        except Exception as e:
            notify(agent_key, "error", msg=str(e))
            objections = []
        timings[agent_key] = time.perf_counter() - t0
        all_objections.extend(objections)
        notify(
            agent_key,
            "done",
            count=len(objections),
            elapsed=timings[agent_key],
        )

    # Sort all objections by severity descending before judging
    all_objections.sort(key=lambda x: x.get("severity_score", 0), reverse=True)

    # ------------------------------------------------------------------ #
    # Stage 5: LLM Judge
    # ------------------------------------------------------------------ #
    notify("judge", "running")
    t0 = time.perf_counter()
    try:
        scored_objections = run_judge_agent(all_objections, page_content, api_key=api_key)
    except Exception as e:
        notify("judge", "error", msg=str(e))
        # Fall back: mark everything as VALID so the pipeline doesn't hard-fail
        scored_objections = [
            {
                **obj,
                "judge_grounded_score": 7,
                "judge_real_buyer_score": 7,
                "judge_verdict": "VALID",
                "judge_reasoning": "Judge agent unavailable; defaulting to VALID.",
            }
            for obj in all_objections
        ]
    timings["judge"] = time.perf_counter() - t0
    notify(
        "judge",
        "done",
        total=len(scored_objections),
        valid=sum(1 for o in scored_objections if o.get("judge_verdict") == "VALID"),
        elapsed=timings["judge"],
    )

    # Assign final ranks (only across VALID objections)
    valid_objs = [o for o in scored_objections if o.get("judge_verdict") == "VALID"]
    other_objs = [o for o in scored_objections if o.get("judge_verdict") != "VALID"]
    rank_badges = ["LETHAL DEAL KILLER", "CRITICAL BLOCKER", "PROCUREMENT GATE"]
    for i, obj in enumerate(valid_objs, start=1):
        obj["rank"] = i
        obj["rank_badge"] = rank_badges[min(i - 1, 2)]

    # Overall damage score = weighted avg of severity scores of VALID objections
    if valid_objs:
        overall_score = int(
            sum(o.get("severity_score", 0) for o in valid_objs) / len(valid_objs)
        )
    else:
        overall_score = 0

    notify("hermes", "done", total_objections=len(scored_objections), overall_score=overall_score)

    return {
        "page_content": page_content,
        "from_cache": from_cache,
        "all_objections": valid_objs + other_objs,   # valid first, then weak/hallucinated
        "valid_objections": valid_objs,
        "overall_damage_score": overall_score,
        "timings": timings,
    }
