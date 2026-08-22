import asyncio
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="The Adversarial Buyer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom High-Contrast Styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #888888;
        margin-bottom: 2rem;
    }
    /* Make text input prominent */
    div[data-testid="stTextInput"] input {
        font-size: 1.25rem;
        padding: 0.75rem 1rem;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">THE ADVERSARIAL BUYER</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Simulate hostile enterprise procurement committees against your pricing page before your buyers do.</div>', unsafe_allow_html=True)

from services.scraper import fetch_page


# 2. Page Extraction Pipeline
def run_extraction_pipeline(url: str) -> str:
    """Fetch clean markdown content using Jina Reader scraper service (with disk cache)."""
    return fetch_page(url)


# 3. Mocked Objection Data (CFO, CISO, VP Engineering)
MOCK_OBJECTIONS = [
    {
        "persona": "Chief Financial Officer (CFO)",
        "role_badge": "Finance & Procurement",
        "severity_score": 94,
        "severity_label": "Critical Risk (94/100)",
        "verbatim_quote": '"Contact Us for Custom Pricing" with mandatory annual minimum commitments hidden behind an opaque sales demo wall.',
        "rationale": "Enterprise procurement requires predictable consumption modeling and transparent tiered boundaries. Forcing sales calls without baseline unit economics signals aggressive lock-in risk, hidden platform fees, and unpredictable multi-year escalation clauses.",
        "recommended_fix": "Publish transparent tier calculators with explicit volumetric discount curves and SLA multipliers to establish immediate trust and bypass lengthy pre-qualification friction.",
    },
    {
        "persona": "Chief Information Security Officer (CISO)",
        "role_badge": "Security & Compliance",
        "severity_score": 88,
        "severity_label": "High Risk (88/100)",
        "verbatim_quote": '"Enterprise tier includes SSO, Audit Logs, and SOC2 Report access upon request."',
        "rationale": "Treating core security primitives (SAML 2.0 / SCIM / Immutable Audit Logs) as premium 'Enterprise Tax' addons triggers immediate vendor assessment red flags. It indicates security is treated as a commercial upsell rather than a foundational architecture standard.",
        "recommended_fix": "Unbundle SAML SSO and tenant audit logging into the base tier; monetize advanced governance, custom key management (BYOK), and data residency guarantees instead.",
    },
    {
        "persona": "VP of Engineering",
        "role_badge": "Technical Due Diligence",
        "severity_score": 82,
        "severity_label": "High Risk (82/100)",
        "verbatim_quote": '"Unlimited API calls* (*subject to unspecified Fair Use Policy throttling thresholds)."',
        "rationale": "Ambiguous throttling guarantees introduce critical production outage risks for downstream microservices. Unspecified rate limits without hard burst capacities or webhook retry SLAs block architectural sign-off during technical due diligence.",
        "recommended_fix": "Replace vague 'Fair Use' terminology with deterministic rate limits (e.g., 5,000 req/min with burst up to 10k req/min) and publish standard status page SLAs.",
    },
]

# 4. Input Section
target_url = st.text_input(
    "Target Pricing Page URL",
    placeholder="https://acme.com/pricing",
    help="Enter the full URL of the public pricing or packaging page you want to stress-test.",
)

scan_submitted = st.button("Scan Pricing Page", type="primary", use_container_width=True)

# 5. Execution & Visual Hierarchy
if scan_submitted:
    if not target_url:
        st.warning("Please enter a valid pricing page URL to initiate adversarial analysis.")
    else:
        # Progress State using st.status() cycling through required phases
        with st.status("Initiating Adversarial Audit...", expanded=True) as status_box:
            st.write("Initializing stealth browser...")
            run_extraction_pipeline(target_url)
            
            st.write("Extracting DOM...")
            asyncio.run(asyncio.sleep(0.8))
            
            st.write("Running Adversarial Personas...")
            asyncio.run(asyncio.sleep(0.8))
            
            status_box.update(
                label="Adversarial Audit Complete — Hostile Committee Findings Ready",
                state="complete",
                expanded=False,
            )

        st.divider()

        # Visual Hierarchy: Overall Deal Damage Score Metric
        st.metric(
            label="Overall Deal Damage Score",
            value="88 / 100",
            delta="Severe Enterprise Friction (-18 pts Win Rate)",
            delta_color="inverse",
            help="Weighted aggregate resistance score across CFO, CISO, and VP Engineering committee gates.",
        )

        st.markdown("### Hostile Committee Objections")

        # Visual Hierarchy: Objection Cards inside Bordered Containers
        for item in MOCK_OBJECTIONS:
            with st.container(border=True):
                col_left, col_right = st.columns([1, 2.5], gap="medium")

                with col_left:
                    st.subheader(item["persona"])
                    st.caption(f"Domain: {item['role_badge']}")
                    st.metric(
                        label="Severity Score",
                        value=f"{item['severity_score']}/100",
                    )

                with col_right:
                    st.markdown("**Exact Verbatim Quote (The Crime):**")
                    st.error(item["verbatim_quote"], icon="🚨")

                    st.markdown("**Objection Rationale:**")
                    st.write(item["rationale"])

                    st.markdown("**Recommended Fix:**")
                    st.success(item["recommended_fix"], icon="✅")
