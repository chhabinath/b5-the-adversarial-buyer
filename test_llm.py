import json
import time
from services.llm_analyzer import analyze_pricing

SAMPLE_CONTENT = """
# Acme Cloud Pricing
- Free: $0 (100 reqs/day)
- Team: $49/mo (Fair use unmetered)
- Enterprise: Contact us, $50k annual minimum, SAML SSO available only on Enterprise tier, 99.9% uptime.
"""

print("Running test with services.llm_analyzer.analyze_pricing()...")
start_t = time.perf_counter()
result = analyze_pricing(SAMPLE_CONTENT)
elapsed = time.perf_counter() - start_t

print(f"\n[DONE in {elapsed:.2f}s]")
print(f"Overall Deal Damage Score: {result.get('overall_damage_score')}/100")
print(f"Summary: {result.get('deal_damage_summary')}\n")
for item in result.get("objections", []):
    print(f"- [{item['persona']}] Severity: {item['severity_score']}/100")
    print(f"  Verbatim: {item['verbatim_quote']}")
    print(f"  Fix:      {item['recommended_fix']}\n")
