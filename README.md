# ⚡ The Adversarial Buyer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenRouter](https://img.shields.io/badge/AI-OpenRouter-000000)](https://openrouter.ai/)

**A multi-agent hostile procurement simulator that stress-tests your SaaS pricing page before your buyers do.**

---

## 🎯 The Problem

When B2B SaaS companies transition from SMB/PLG upmarket to enterprise, their deals start dying. Founders think it's the product. Sales thinks it's the competition.

**The truth: Deals die on the pricing page, before the first sales call.**

Enterprise procurement committees—comprising the CFO, CISO, and VP of Engineering—evaluate your public pricing page to decide if you are a safe vendor. They look for:
- **CFOs:** "Custom" pricing with no budget anchor, hidden minimums, lock-in clauses.
- **CISOs:** Security features (like SSO or audit logs) monetized as expensive upsells rather than baseline infrastructure.
- **VP Eng:** Vague "fair use" API throttling with no hard SLAs.

If your page has these traps, the committee kills the deal. The GTM team never finds out why.

## 💡 The Solution

**The Adversarial Buyer** is an autonomous AI system that emulates this hostile procurement committee. 

You give it your pricing page URL. It reads the live site and unleashes three distinct, specialized AI agents (CFO, CISO, VP Eng) to attack it. A fourth LLM Judge fact-checks every objection against the actual text on your page. Finally, a human-in-the-loop review lets you curate the results into a boardroom-ready report containing the exact objections that will kill your deal—and how to fix them.

## 🚀 How It Works (The Multi-Agent Pipeline)

1. **🟣 Hermes (The Orchestrator):** Coordinates the entire pipeline and provides real-time status updates to the UI.
2. **🔵 Scraper Agent:** Uses the Jina Reader API to fetch the live URL and extract clean, plain-text Markdown. It caches results locally (via SHA1 hashing) for instant re-runs.
3. **💰🔐⚙️ The Buyer Agents:** 
   - **CFO Agent:** Attacks finance and procurement vulnerabilities.
   - **CISO Agent:** Attacks security and compliance gaps.
   - **VP Eng Agent:** Attacks technical and SLA ambiguities.
   *(Each agent makes a separate LLM call with a hyper-focused persona prompt to ensure deep, surgical analysis rather than generic feedback.)*
4. **⚖️ LLM Judge Agent:** An independent AI that fact-checks the buyer agents. It scores every generated objection (0-10) on:
   - **Groundedness:** Is this objection citing a real line from the page? (Catches hallucinations).
   - **Realism:** Would a real enterprise buyer actually raise this?
5. **🧑 Human-in-the-Loop:** Before the final report is compiled, a human reviews the judge's scores, approving or dismissing objections to ensure total relevance.

## 📊 Success Metric

**Target:** ≥ 3 actionable, deal-killing objections surfaced per pricing page audit.
*Every objection must be tied to a verbatim or near-verbatim quote from the actual page.*

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit (High-contrast, reactive dashboard with live agent status).
- **Orchestration:** Custom Python multi-agent framework (`agents/`).
- **Scraping:** Jina Reader API (`r.jina.ai`).
- **LLM Provider:** OpenRouter (Pure `httpx` implementation, no heavy SDKs).
- **Default Model:** `nvidia/nemotron-3.5-lightning:free` (with automatic failover to `dots-studio` and `liquid` models).

## 💻 Local Setup

### Prerequisites
- Python 3.10+
- An [OpenRouter](https://openrouter.ai/) API Key (Free tier works perfectly).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Satyam6024/b5-the-adversarial-buyer.git
   cd b5-the-adversarial-buyer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Create a `.env` file in the root directory and add your OpenRouter API key:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxx
   ```

4. **Run the App:**
   ```bash
   streamlit run app.py
   ```

### Running Tests
The project includes automated tests for the scraper/caching layer and the LLM API connectivity.
```bash
python test_scraper.py
python test_llm.py
```

---

## 📁 Project Structure

```text
├── app.py                      # Main Streamlit UI (Pipeline, Human Review, Report)
├── agents/                     # Multi-Agent Framework
│   ├── hermes.py               # Pipeline orchestrator
│   ├── buyer_agents.py         # CFO, CISO, and VP Eng personas
│   └── judge_agent.py          # Fact-checking and scoring LLM
├── services/                   
│   ├── scraper.py              # Jina Reader integration & SHA1 caching
│   ├── openrouter_client.py    # Shared robust HTTP client for LLM calls
│   └── llm_analyzer.py         # Legacy single-call fallback analyzer
├── cache/                      # Local disk cache for scraped pages
├── knowledge_base.md           # Deep-dive architecture & engineering documentation
└── test_*.py                   # Unit tests
```

---
*Built to help founders survive the enterprise boardroom.*
