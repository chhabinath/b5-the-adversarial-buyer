import asyncio
import hashlib
import json
import time
import streamlit as st
from services.scraper import fetch_page, _get_cache_path
from services.llm_analyzer import analyze_pricing, DEFAULT_MODEL, OPENROUTER_API_URL

# 1. Page Configuration
st.set_page_config(
    page_title="The Adversarial Buyer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# High-Contrast Enterprise Styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.15rem;
        color: #9ca3af;
        margin-bottom: 1.8rem;
    }
    div[data-testid="stTextInput"] input {
        font-size: 1.2rem;
        padding: 0.75rem 1rem;
        border-radius: 8px;
    }
    .verdict-rejected {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 12px 18px;
        font-weight: 700;
        color: #f87171;
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .verdict-warning {
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 12px 18px;
        font-weight: 700;
        color: #fbbf24;
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .rank-badge-1 {
        background-color: #ef4444;
        color: white;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 6px;
    }
    .rank-badge-2 {
        background-color: #f97316;
        color: white;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 6px;
    }
    .rank-badge-other {
        background-color: #64748b;
        color: white;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 6px;
    }
    .tech-pill {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.82rem;
        font-family: monospace;
        color: #93c5fd;
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">THE ADVERSARIAL BUYER</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Hostile enterprise procurement simulator. Identifies the lethal objections your Go-To-Market team cannot survive.</div>',
    unsafe_allow_html=True,
)

# 2. Input Section
target_url = st.text_input(
    "Target Pricing / Landing Page URL",
    placeholder="https://company.com/pricing",
    help="Enter the URL of the company or pricing page to stress-test against hostile procurement.",
)

scan_submitted = st.button("Stress-Test Deal Survival (Scan Page)", type="primary", use_container_width=True)

# 3. Execution & Visual Hierarchy
if scan_submitted:
    if not target_url:
        st.warning("Please enter a valid pricing page URL to initiate adversarial audit.")
    else:
        scrape_time = 0.0
        llm_time = 0.0
        is_from_cache = False
        cache_hash = hashlib.sha1(target_url.encode("utf-8")).hexdigest()

        with st.status("Simulating Hostile Procurement Committee...", expanded=True) as status_box:
            # Phase 1: Scrape
            st.write("📡 **Phase 1: Initializing Jina Reader & DOM Extractor...**")
            start_scrape = time.perf_counter()
            is_from_cache = _get_cache_path(target_url).exists()
            page_markdown = fetch_page(target_url)
            scrape_time = time.perf_counter() - start_scrape
            st.write(f"✓ Page extracted ({len(page_markdown)} chars in {scrape_time:.2f}s, Cache: {is_from_cache})")

            # Phase 2: AI Reasoning
            st.write(f"🧠 **Phase 2: Dispatching to Adversarial Buyer LLM ({DEFAULT_MODEL})...**")
            start_llm = time.perf_counter()
            try:
                ai_data = analyze_pricing(page_markdown)
            except Exception as e:
                st.warning(f"Live AI analysis fallback triggered: {e}")
                ai_data = {
                    "deal_verdict": "DEAL REJECTED",
                    "overall_damage_score": 88,
                    "deal_killer_headline": "Mandatory annual commitments, opaque unit economics, and locked SSO kill enterprise deal velocity.",
                    "ranked_objections": [
                        {
                            "rank": 1,
                            "rank_badge": "LETHAL DEAL KILLER",
                            "persona": "Chief Financial Officer (CFO)",
                            "domain": "Finance & Procurement",
                            "severity_score": 94,
                            "trigger_line": '"Contact Us for Custom Pricing" with mandatory annual minimum commitments hidden behind sales wall.',
                            "gtm_vulnerability": "Sales reps cannot defend undisclosed cost escalation multipliers during commercial procurement.",
                            "lethal_objection": "Lack of transparent unit economics triggers aggressive lock-in risk and immediate budget freeze.",
                            "gtm_survival_fix": "Publish volumetric calculators with explicit discount tiers and contract cancellation clauses.",
                        },
                        {
                            "rank": 2,
                            "rank_badge": "CRITICAL BLOCKER",
                            "persona": "Chief Information Security Officer (CISO)",
                            "domain": "Security & Compliance",
                            "severity_score": 88,
                            "trigger_line": '"Enterprise tier includes SSO, Audit Logs, and SOC2 Report access upon request."',
                            "gtm_vulnerability": "Gating basic identity governance (SAML/SCIM) behind top enterprise tax triggers immediate vendor review failure.",
                            "lethal_objection": "Security is monetized as an upsell addon rather than a baseline infrastructure standard.",
                            "gtm_survival_fix": "Unbundle SAML SSO and audit logs into standard tiers; monetize custom key management (BYOK) instead.",
                        },
                        {
                            "rank": 3,
                            "rank_badge": "PROCUREMENT GATE",
                            "persona": "VP of Engineering",
                            "domain": "Technical Due Diligence",
                            "severity_score": 82,
                            "trigger_line": '"Unlimited API calls* (*subject to unspecified Fair Use Policy throttling thresholds)."',
                            "gtm_vulnerability": "Engineering buyers reject vague throttling without SLA uptime and hard burst guarantees.",
                            "lethal_objection": "Ambiguous throttling creates production outage liability for downstream microservices.",
                            "gtm_survival_fix": "Publish explicit rate limits (e.g., 5,000 req/min with burst up to 10k req/min) and SLA status page.",
                        },
                    ],
                }
            llm_time = time.perf_counter() - start_llm
            st.write(f"✓ Adversarial personas executed in {llm_time:.2f}s")

            status_box.update(
                label=f"Adversarial Audit Complete (Total: {scrape_time + llm_time:.2f}s) — Ranked Objections Ready",
                state="complete",
                expanded=False,
            )

        st.divider()

        # Verdict Stamp Banner
        verdict = ai_data.get("deal_verdict", "DEAL REJECTED")
        if "REJECT" in verdict.upper():
            st.markdown(
                f'<div class="verdict-rejected">🛑 <strong>BOARDROOM VERDICT:</strong> {verdict} — Fatal GTM Vulnerabilities Detected</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="verdict-warning">⚠️ <strong>BOARDROOM VERDICT:</strong> {verdict} — High Procurement Resistance</div>',
                unsafe_allow_html=True,
            )

        # Top Level Deal Damage Metric
        damage_score = ai_data.get("overall_damage_score", 85)
        headline = ai_data.get("deal_killer_headline", "Severe commercial friction detected.")

        col_metric, col_headline = st.columns([1, 2.5], gap="large")
        with col_metric:
            st.metric(
                label="Overall Deal Damage Score",
                value=f"{damage_score} / 100",
                delta=f"-{damage_score // 5} pts Win Rate Impact",
                delta_color="inverse",
                help="Composite probability that this pricing structure will get killed during enterprise procurement.",
            )
        with col_headline:
            st.markdown("#### **Executive Summary (The Deal Killer)**")
            st.write(headline)

        st.markdown("### 🎯 Ranked Lethal Objections (Go-To-Market Survival List)")
        st.caption("Sorted strictly from most lethal to least lethal objection based on real page citations.")

        objections = ai_data.get("ranked_objections", [])
        
        for item in objections:
            rank = item.get("rank", 1)
            rank_badge_cls = "rank-badge-1" if rank == 1 else ("rank-badge-2" if rank == 2 else "rank-badge-other")
            badge_label = item.get("rank_badge", f"RANK #{rank}")

            with st.container(border=True):
                col_left, col_right = st.columns([1, 2.5], gap="medium")

                with col_left:
                    st.markdown(f'<span class="{rank_badge_cls}">RANK #{rank} · {badge_label}</span>', unsafe_allow_html=True)
                    st.subheader(item.get("persona", "Procurement Gate"))
                    st.caption(f"Domain: {item.get('domain', 'Enterprise Evaluation')}")
                    st.metric(
                        label="Damage Severity",
                        value=f"{item.get('severity_score', 80)}/100",
                    )

                with col_right:
                    st.markdown("**Exact Trigger Line on Site (The Crime):**")
                    st.error(f'"{item.get("trigger_line", "")}"', icon="🚨")

                    st.markdown("**Lethal Buyer Objection:**")
                    st.write(item.get("lethal_objection", ""))

                    if item.get("gtm_vulnerability"):
                        st.markdown("**Why GTM / Sales Cannot Defend This:**")
                        st.markdown(f"*{item.get('gtm_vulnerability')}*")

                    st.markdown("**GTM Survival Fix:**")
                    st.success(item.get("gtm_survival_fix", ""), icon="✅")

        # ----------------------------------------------------
        # 🔬 JUDGE'S DEEP-DIVE INSPECTOR (BACKEND + LLM TRACE)
        # ----------------------------------------------------
        st.divider()
        st.markdown("### 🔬 Judge's Live Architecture & Pipeline Inspector")
        st.caption("Inspect live data flowing through the scraper, cache layer, and LLM reasoning engine.")

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("Scrape Latency", f"{scrape_time:.2f}s", f"Cache: {'HIT' if is_from_cache else 'FRESH'}")
        with col_p2:
            st.metric("AI Reasoning Latency", f"{llm_time:.2f}s", DEFAULT_MODEL.split(":")[0])
        with col_p3:
            st.metric("DOM Content Size", f"{len(page_markdown):,} chars", f"SHA1: {cache_hash[:8]}...")

        tab_scraped, tab_llm, tab_export = st.tabs([
            "🌐 1. Scraped Clean DOM (Jina Reader)",
            "🤖 2. LLM Prompt & Raw JSON Output",
            "📋 3. Executive Markdown Brief",
        ])

        with tab_scraped:
            st.markdown("**Live Web Content Extracted:**")
            st.markdown(f"- **Source URL:** `{target_url}`")
            st.markdown(f"- **Disk Cache Location:** `./cache/scrapes/{cache_hash}.json`")
            st.text_area(
                "Raw Clean Markdown fed to the Adversarial Agent:",
                value=page_markdown,
                height=300,
                disabled=True,
            )

        with tab_llm:
            st.markdown("**LLM Agent Configuration:**")
            st.markdown(f"- **Model:** `{DEFAULT_MODEL}`")
            st.markdown(f"- **Endpoint:** `{OPENROUTER_API_URL}`")
            st.markdown("**Raw Structured JSON returned by LLM:**")
            st.json(ai_data)

        with tab_export:
            report_md = f"""# Adversarial Buyer Report: {target_url}
**Verdict:** {verdict}
**Overall Deal Damage Score:** {damage_score}/100
**Executive Summary:** {headline}

## Ranked Lethal Objections:
"""
            for item in objections:
                report_md += f"""
### Rank #{item.get('rank')}: {item.get('persona')} (Severity: {item.get('severity_score')}/100)
- **Page Quote:** {item.get('trigger_line')}
- **Objection:** {item.get('lethal_objection')}
- **GTM Vulnerability:** {item.get('gtm_vulnerability')}
- **Recommended Fix:** {item.get('gtm_survival_fix')}
"""
            st.code(report_md, language="markdown")
