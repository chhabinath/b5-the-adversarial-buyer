import hashlib
import time
import streamlit as st
from agents.hermes import run_pipeline, AGENT_META
from services.openrouter_client import DEFAULT_MODEL, OPENROUTER_API_URL

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Adversarial Buyer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global Styles ────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-title {
        font-size: 2.8rem; font-weight: 900;
        letter-spacing: -0.04em; margin-bottom: 0.2rem;
        background: linear-gradient(135deg, #f97316, #ef4444);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub-title { font-size: 1.1rem; color: #9ca3af; margin-bottom: 1.5rem; }

    /* Agent status cards */
    .agent-card {
        display: flex; align-items: center; gap: 12px;
        padding: 10px 16px; border-radius: 8px; margin-bottom: 6px;
        background: #0f172a; border: 1px solid #1e293b;
        font-size: 0.92rem;
    }
    .agent-card.waiting  { border-color: #334155; color: #64748b; }
    .agent-card.running  { border-color: #f59e0b; color: #fbbf24; background: rgba(245,158,11,0.08); }
    .agent-card.done     { border-color: #22c55e; color: #86efac; background: rgba(34,197,94,0.07); }
    .agent-card.error    { border-color: #ef4444; color: #f87171; background: rgba(239,68,68,0.08); }

    /* Verdict banners */
    .verdict-rejected {
        background: rgba(239,68,68,0.12); border: 1px solid #ef4444;
        border-radius: 8px; padding: 14px 20px; font-weight: 700;
        color: #f87171; font-size: 1.3rem; margin-bottom: 1.5rem;
    }
    .verdict-warning {
        background: rgba(245,158,11,0.12); border: 1px solid #f59e0b;
        border-radius: 8px; padding: 14px 20px; font-weight: 700;
        color: #fbbf24; font-size: 1.3rem; margin-bottom: 1.5rem;
    }

    /* Rank badges */
    .badge { padding: 3px 10px; border-radius: 4px; font-size: 0.72rem;
             font-weight: 800; letter-spacing: 0.06em; display: inline-block; margin-bottom: 6px; }
    .badge-1 { background: #ef4444; color: #fff; }
    .badge-2 { background: #f97316; color: #fff; }
    .badge-n { background: #64748b; color: #fff; }

    /* Judge score pills */
    .judge-pill {
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 700; margin-right: 6px;
    }
    .judge-valid { background: rgba(34,197,94,0.2); color: #4ade80; border: 1px solid #22c55e; }
    .judge-weak  { background: rgba(245,158,11,0.2); color: #fbbf24; border: 1px solid #f59e0b; }
    .judge-hall  { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid #ef4444; }

    /* Human review checkboxes */
    .review-header {
        font-size: 1.4rem; font-weight: 800; margin-bottom: 0.5rem; color: #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">⚡ THE ADVERSARIAL BUYER</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Multi-agent hostile procurement simulator · '
    'CFO · CISO · VP Eng · LLM Judge · Human Review</div>',
    unsafe_allow_html=True,
)

# ── Session State Init ────────────────────────────────────────────────────────
for k, v in [
    ("pipeline_result", None),
    ("scanned_url", ""),
    ("agent_states", {}),        # key → {status, info}
    ("approved_indices", None),  # set by human review step
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Input ─────────────────────────────────────────────────────────────────────
target_url = st.text_input(
    "Target Pricing / Landing Page URL",
    placeholder="https://company.com/pricing",
    help="Paste the live URL of any company's pricing page.",
)
scan_btn = st.button("⚡ Stress-Test Deal Survival", type="primary", use_container_width=True)

# ── Reset on new URL ──────────────────────────────────────────────────────────
if scan_btn and target_url and target_url != st.session_state.scanned_url:
    st.session_state.pipeline_result = None
    st.session_state.approved_indices = None
    st.session_state.agent_states = {}
    st.session_state.scanned_url = target_url

# ── Pipeline Execution ────────────────────────────────────────────────────────
if scan_btn and target_url and st.session_state.pipeline_result is None:
    st.divider()
    st.markdown("### 🤖 Agent Pipeline — Live Status")
    st.caption("Watch each agent activate in real time.")

    # One empty placeholder per agent
    slots = {meta["key"]: st.empty() for meta in AGENT_META}

    def render_card(key: str, status: str, label: str = "", extra: str = ""):
        meta = next(m for m in AGENT_META if m["key"] == key)
        icon_map = {"waiting": "⏳", "running": "🟡", "done": "✅", "error": "❌"}
        icon = icon_map.get(status, "⏳")
        line2 = f"<br><small style='color:#94a3b8'>{extra}</small>" if extra else ""
        html = (
            f'<div class="agent-card {status}">'
            f'{meta["icon"]} <strong>{meta["name"]}</strong> — {label or meta["desc"]}'
            f'{line2}</div>'
        )
        slots[key].markdown(html, unsafe_allow_html=True)

    # Initialise all as waiting
    for meta in AGENT_META:
        render_card(meta["key"], "waiting")

    def on_status(key: str, status: str, info: dict):
        st.session_state.agent_states[key] = {"status": status, "info": info}
        label_map = {
            "running": "Analyzing...",
            "done": f"Done ({info.get('elapsed', 0):.1f}s)"
                    + (f" · {info.get('count','')} objections" if "count" in info else "")
                    + (f" · {info.get('chars',0):,} chars" if "chars" in info else "")
                    + (f" · {info.get('valid',0)} valid / {info.get('total',0)} total" if "valid" in info else ""),
            "error": f"Error: {info.get('msg', 'unknown')}",
        }
        extra_map = {
            "scraper": f"Cache: {'HIT ✓' if info.get('from_cache') else 'FRESH'}",
            "judge":   f"Filtered: {info.get('total',0) - info.get('valid',0)} hallucinated / weak",
        }
        render_card(
            key,
            status,
            label=label_map.get(status, ""),
            extra=extra_map.get(key, "") if status == "done" else "",
        )

    # Run Hermes
    try:
        result = run_pipeline(target_url, on_status=on_status)
        st.session_state.pipeline_result = result
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.stop()

    st.rerun()

# ── Human-in-the-Loop Review ─────────────────────────────────────────────────
if (
    st.session_state.pipeline_result is not None
    and st.session_state.approved_indices is None
):
    result = st.session_state.pipeline_result
    all_objs = result["all_objections"]

    st.divider()

    # Replay agent status panel (from saved states)
    if st.session_state.agent_states:
        with st.expander("🤖 Agent Pipeline — Completed", expanded=False):
            for meta in AGENT_META:
                state = st.session_state.agent_states.get(meta["key"], {})
                status = state.get("status", "done")
                info = state.get("info", {})
                extra = ""
                if meta["key"] == "scraper":
                    extra = f"Cache: {'HIT ✓' if info.get('from_cache') else 'FRESH'}"
                elif meta["key"] == "judge":
                    extra = f"Filtered: {info.get('total',0) - info.get('valid',0)} weak/hallucinated"
                label = f"Done ({info.get('elapsed', 0):.1f}s)" if status == "done" else status.title()
                html = (
                    f'<div class="agent-card {status}">'
                    f'{meta["icon"]} <strong>{meta["name"]}</strong> — {label}'
                    + (f"<br><small style='color:#94a3b8'>{extra}</small>" if extra else "")
                    + "</div>"
                )
                st.markdown(html, unsafe_allow_html=True)

    # Human review panel
    st.markdown('<div class="review-header">🧑 Human-in-the-Loop Review</div>', unsafe_allow_html=True)
    st.markdown(
        "The **LLM Judge** has scored every objection. "
        "**You** decide which ones make it into the final boardroom report. "
        "Uncheck anything you believe is irrelevant or not applicable to your situation."
    )
    st.caption("Only checked objections will appear in the final ranked report.")

    approval_checks = {}

    for i, obj in enumerate(all_objs):
        verdict = obj.get("judge_verdict", "VALID")
        grounded = obj.get("judge_grounded_score", 7)
        realism = obj.get("judge_real_buyer_score", 7)
        persona = obj.get("persona", "Unknown")
        trigger = obj.get("trigger_line", "")[:80]
        reasoning = obj.get("judge_reasoning", "")

        # Color pill
        pill_cls = {"VALID": "judge-valid", "WEAK": "judge-weak"}.get(verdict, "judge-hall")
        pill_html = (
            f'<span class="judge-pill {pill_cls}">{verdict}</span>'
            f'<span class="judge-pill" style="background:#1e293b;color:#94a3b8;border:1px solid #334155">'
            f'Ground {grounded}/10 · Realism {realism}/10</span>'
        )

        with st.container(border=True):
            col_chk, col_info = st.columns([0.7, 5])
            with col_chk:
                # Pre-check VALID objections, uncheck weak/hallucinated
                default = verdict == "VALID"
                approval_checks[i] = st.checkbox(
                    "Include",
                    value=default,
                    key=f"approve_{i}",
                    label_visibility="collapsed",
                )
            with col_info:
                st.markdown(pill_html, unsafe_allow_html=True)
                st.markdown(f"**[{persona}]** — *\"{trigger}...\"*")
                st.caption(f"⚖️ Judge says: {reasoning}")

    compile_btn = st.button(
        "📋 Compile Final Boardroom Report →",
        type="primary",
        use_container_width=True,
    )

    if compile_btn:
        approved = [i for i, checked in approval_checks.items() if checked]
        st.session_state.approved_indices = approved
        st.rerun()

# ── Final Report ──────────────────────────────────────────────────────────────
if (
    st.session_state.pipeline_result is not None
    and st.session_state.approved_indices is not None
):
    result = st.session_state.pipeline_result
    all_objs = result["all_objections"]
    approved_indices = st.session_state.approved_indices
    final_objs = [all_objs[i] for i in approved_indices]

    # Re-rank approved objections
    final_objs.sort(key=lambda x: x.get("severity_score", 0), reverse=True)
    rank_badges = ["LETHAL DEAL KILLER", "CRITICAL BLOCKER", "PROCUREMENT GATE"]
    for i, obj in enumerate(final_objs, start=1):
        obj["rank"] = i
        obj["rank_badge"] = rank_badges[min(i - 1, 2)]

    overall_score = (
        int(sum(o.get("severity_score", 0) for o in final_objs) / len(final_objs))
        if final_objs else 0
    )

    st.divider()

    # ── Agent summary (collapsed) ─────────────────────────────────────────
    if st.session_state.agent_states:
        with st.expander("🤖 Agent Pipeline — Completed", expanded=False):
            for meta in AGENT_META:
                state = st.session_state.agent_states.get(meta["key"], {})
                status = state.get("status", "done")
                info = state.get("info", {})
                extra = ""
                if meta["key"] == "scraper":
                    extra = f"Cache: {'HIT ✓' if info.get('from_cache') else 'FRESH'}"
                elif meta["key"] == "judge":
                    extra = f"Filtered: {info.get('total',0) - info.get('valid',0)} weak/hallucinated"
                label = f"Done ({info.get('elapsed', 0):.1f}s)" if status == "done" else status.title()
                html = (
                    f'<div class="agent-card {status}">'
                    f'{meta["icon"]} <strong>{meta["name"]}</strong> — {label}'
                    + (f"<br><small style='color:#94a3b8'>{extra}</small>" if extra else "")
                    + "</div>"
                )
                st.markdown(html, unsafe_allow_html=True)

    # ── Verdict banner ────────────────────────────────────────────────────
    if overall_score >= 70:
        verdict_label = "DEAL REJECTED"
        st.markdown(
            f'<div class="verdict-rejected">🛑 <strong>BOARDROOM VERDICT:</strong> '
            f'{verdict_label} — Fatal GTM Vulnerabilities Detected</div>',
            unsafe_allow_html=True,
        )
    else:
        verdict_label = "DEAL AT RISK"
        st.markdown(
            f'<div class="verdict-warning">⚠️ <strong>BOARDROOM VERDICT:</strong> '
            f'{verdict_label} — High Procurement Resistance</div>',
            unsafe_allow_html=True,
        )

    # ── Damage score + human approval summary ─────────────────────────────
    col_score, col_meta = st.columns([1, 2.5], gap="large")
    with col_score:
        st.metric(
            "Overall Deal Damage Score",
            f"{overall_score} / 100",
            delta=f"-{overall_score // 5} pts Win Rate Impact",
            delta_color="inverse",
        )
    with col_meta:
        st.markdown("#### Human-Approved Objections")
        total = len(all_objs)
        approved_count = len(final_objs)
        skipped = total - approved_count
        st.write(
            f"**{approved_count}** objections approved · **{skipped}** dismissed by human review · "
            f"**{sum(1 for o in all_objs if o.get('judge_verdict') != 'VALID')}** filtered by LLM Judge"
        )
        col_r, col_n = st.columns(2)
        with col_r:
            if st.button("🔄 Re-run Human Review", use_container_width=True):
                st.session_state.approved_indices = None
                st.rerun()
        with col_n:
            if st.button("🆕 Scan New URL", use_container_width=True):
                st.session_state.pipeline_result = None
                st.session_state.approved_indices = None
                st.session_state.agent_states = {}
                st.session_state.scanned_url = ""
                st.rerun()

    # ── Ranked Objections ─────────────────────────────────────────────────
    st.markdown("### 🎯 Ranked Lethal Objections (Human-Approved · Judge-Validated)")
    st.caption("Only objections you approved with judge realism ≥ 6/10.")

    for obj in final_objs:
        rank = obj.get("rank", 1)
        badge_cls = "badge-1" if rank == 1 else ("badge-2" if rank == 2 else "badge-n")
        badge_txt = obj.get("rank_badge", f"RANK #{rank}")
        grounded = obj.get("judge_grounded_score", "-")
        realism = obj.get("judge_real_buyer_score", "-")

        with st.container(border=True):
            col_left, col_right = st.columns([1, 2.5], gap="medium")

            with col_left:
                st.markdown(
                    f'<span class="badge {badge_cls}">RANK #{rank} · {badge_txt}</span>',
                    unsafe_allow_html=True,
                )
                st.subheader(obj.get("persona", "Buyer"))
                st.caption(f"Domain: {obj.get('domain', '')}")
                st.metric("Damage Severity", f"{obj.get('severity_score', 0)}/100")
                # Judge scores
                g_color = "#4ade80" if grounded >= 7 else "#fbbf24"
                r_color = "#4ade80" if realism >= 7 else "#fbbf24"
                st.markdown(
                    f"**LLM Judge:** "
                    f'<span style="color:{g_color}">Ground {grounded}/10</span> · '
                    f'<span style="color:{r_color}">Realism {realism}/10</span>',
                    unsafe_allow_html=True,
                )
                st.caption(f"_{obj.get('judge_reasoning', '')}_")

            with col_right:
                st.markdown("**Exact Trigger Line on Site (The Crime):**")
                st.error(f'"{obj.get("trigger_line", "")}"', icon="🚨")

                st.markdown("**Lethal Buyer Objection:**")
                st.write(obj.get("lethal_objection", ""))

                if obj.get("gtm_vulnerability"):
                    st.markdown("**Why GTM / Sales Cannot Defend This:**")
                    st.markdown(f"*{obj.get('gtm_vulnerability')}*")

                st.markdown("**GTM Survival Fix:**")
                st.success(obj.get("gtm_survival_fix", ""), icon="✅")

    # ── Judge's Inspector Tabs ────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔬 Judge's Live Architecture & Pipeline Inspector")
    st.caption("Full transparency: raw data flowing through every layer of the system.")

    page_content = result.get("page_content", "")
    timings = result.get("timings", {})
    cache_hash = hashlib.sha1(st.session_state.scanned_url.encode()).hexdigest()

    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        st.metric("Scrape", f"{timings.get('scraper', 0):.2f}s",
                  f"Cache: {'HIT' if result.get('from_cache') else 'FRESH'}")
    with col_t2:
        st.metric("CFO Agent", f"{timings.get('cfo', 0):.2f}s")
    with col_t3:
        st.metric("CISO + VP Eng", f"{timings.get('ciso', 0) + timings.get('vpeng', 0):.2f}s")
    with col_t4:
        st.metric("LLM Judge", f"{timings.get('judge', 0):.2f}s")

    tab_dom, tab_agents, tab_judge, tab_export = st.tabs([
        "🌐 1. Scraped DOM",
        "🤖 2. Raw Agent Output",
        "⚖️ 3. Judge Scores",
        "📋 4. Export Brief",
    ])

    with tab_dom:
        st.markdown(f"- **Source:** `{st.session_state.scanned_url}`")
        st.markdown(f"- **Cache file:** `./cache/scrapes/{cache_hash}.json`")
        st.text_area("Clean Markdown fed to all agents:", value=page_content, height=300, disabled=True)

    with tab_agents:
        st.markdown("All objections from all buyer agents (before human review):")
        st.json(result["all_objections"])

    with tab_judge:
        st.markdown("**LLM Judge Scores per Objection:**")
        judge_rows = [
            {
                "Agent": obj.get("agent", "").upper(),
                "Persona": obj.get("persona", ""),
                "Grounded": obj.get("judge_grounded_score", "-"),
                "Realism": obj.get("judge_real_buyer_score", "-"),
                "Verdict": obj.get("judge_verdict", ""),
                "Reasoning": obj.get("judge_reasoning", ""),
            }
            for obj in result["all_objections"]
        ]
        st.dataframe(judge_rows, use_container_width=True)
        st.markdown("**Model & Endpoint:**")
        st.markdown(f"- `{DEFAULT_MODEL}` via `{OPENROUTER_API_URL}`")

    with tab_export:
        url_display = st.session_state.scanned_url
        report_md = f"# Adversarial Buyer Report: {url_display}\n\n"
        report_md += f"**Verdict:** {verdict_label}\n"
        report_md += f"**Overall Deal Damage Score:** {overall_score}/100\n"
        report_md += f"**Human-Approved Objections:** {len(final_objs)} / {len(all_objs)} total\n\n"
        report_md += "## Ranked Lethal Objections\n"
        for obj in final_objs:
            report_md += f"\n### Rank #{obj.get('rank')}: {obj.get('persona')} (Severity: {obj.get('severity_score')}/100)\n"
            report_md += f"- **Judge:** Grounded {obj.get('judge_grounded_score')}/10 · Realism {obj.get('judge_real_buyer_score')}/10\n"
            report_md += f"- **Page Quote:** {obj.get('trigger_line')}\n"
            report_md += f"- **Objection:** {obj.get('lethal_objection')}\n"
            report_md += f"- **GTM Vulnerability:** {obj.get('gtm_vulnerability')}\n"
            report_md += f"- **Fix:** {obj.get('gtm_survival_fix')}\n"
        st.code(report_md, language="markdown")
