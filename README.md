# GrowthPilot (AI Commerce Growth Agent)

> *"Your business's AI growth team — it finds the opportunity, decides the play, and runs it."*

GrowthPilot is an autonomous multi-agent AI system for e-commerce sellers that closes the loop between analytics and action. It ingests customer, product, order, session, and cart funnel data; a team of specialized AI agents detects growth opportunities, ranks decisions using transparent scoring, drafts targeted campaign offers, executes them via a mock marketing API under rule-based guardrails, and measures post-campaign outcomes in a closed loop.

---

## 🌟 Key Features

1. **5-Agent Multi-Agent Architecture**:
   - **Insight Agent**: Vectorized RFM customer segmentation, Logistic Regression churn risk scoring, rolling revenue trend slopes, and cart abandonment analytics.
   - **Growth Decision Agent**: Transparent opportunity ranking using `priority_score = expected_impact_revenue * confidence * urgency_factor`.
   - **Campaign & Pricing Agent**: Price elasticity band estimation and AI message copy generation.
   - **Experiment Agent**: Pre vs. Post KPI outcome measurement, statistical z-test evaluation, AI verdict generation, and decision confidence feedback learning.
   - **Orchestrator & Guardrail Agent**: State graph coordinator, rule-based guardrails (Low, Medium, High risk tiers), and audit trail logger.

2. **Deterministic Guardrails Layer**:
   - Discount ceiling checks (max 15%).
   - Weekly budget cap limits ($50,000).
   - Minimum evidence sample size threshold (>=30 customers).
   - Multi-tier human approval workflow with justification inputs for high-risk actions.

3. **Seeded Demo Scenario (§35)**:
   - 6-month synthetic dataset (12,000 customers, 40 products, ~65,000 orders, ~90,000 sessions).
   - Embedded pattern: 18-25 age cohort buying Wireless Earbuds Pro (PROD-001) with a 34% co-purchase interest for Earbud Case & Charging Stand (PROD-002), but only 6% actual conversion and 71% cart abandonment (vs 45% baseline).
   - Automatically surfaces the #1 growth opportunity yielding **₹81,600 expected revenue lift**.

4. **Dashboard Views**:
   - Executive Overview
   - Customer Intelligence
   - Product Intelligence
   - Growth Opportunities
   - Campaign Studio
   - Experiment Results
   - Full Audit Trail Modal

---

## 🚀 Quick Start

### 1. Requirements & Setup

Ensure Python 3.10+ is installed.

```bash
# Clone/navigate to project directory
cd Smart_shop_agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Application (One-Click Launcher)

```bash
python run_growthpilot.py
```

This single command will:
1. Initialize the SQLite database (`growthpilot.db`) and seed the 6-month synthetic dataset.
2. Run the multi-agent detection and decision pipeline.
3. Launch the FastAPI backend server and serve the dashboard UI at **http://127.0.0.1:8000/**.

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/overview` | Executive Overview metrics, charts & top opportunities |
| `GET` | `/api/customers/segments` | RFM customer segment breakdown & CLV |
| `GET` | `/api/customers/churn-risk` | High churn risk customer list with scores |
| `GET` | `/api/products/trends` | Product growth/decline slopes & category trends |
| `GET` | `/api/opportunities` | Ranked growth opportunities list |
| `GET` | `/api/opportunities/{id}` | Detail and evidence snippet for opportunity |
| `POST` | `/api/opportunities/{id}/campaign` | Trigger Campaign Agent to draft proposal |
| `GET` | `/api/campaigns/{id}` | Campaign proposal detail & risk tier |
| `POST` | `/api/campaigns/{id}/approve` | Human approval & mock marketing API execution |
| `GET` | `/api/experiments/{id}` | Post-campaign experiment outcome & AI verdict |
| `GET` | `/api/audit-log` | Full audit log of agent decisions & human actions |

---

## 🎬 3-Minute Hackathon Demo Script

- **0:00–0:20**: *"E-commerce sellers drown in dashboards. GrowthPilot is an autonomous AI agent team that finds opportunities, decides plays, and executes them."*
- **0:20–0:50**: Show **Executive Overview** — point out live revenue/conversion numbers and the #1 flagged opportunity (71% Cart Abandonment on Earbud Stand).
- **0:50–1:30**: Open **Growth Opportunities** — highlight the evidence breakdown (850 customers, 18-25 cohort, 6% conversion vs 22% baseline).
- **1:30–2:00**: Click **"Create Campaign"** — show Campaign Studio with generated 8% offer + AI message copy and Medium Risk badge. Click **"Approve"**.
- **2:00–2:20**: Show the **Mock Marketing API Execution Receipt** generated in real-time.
- **2:20–2:50**: Jump to **Experiment Results** — read the Before → AI Action → After comparison panel and AI verdict sentence (*"Campaign succeeded — conversion nearly tripled..."*).
- **2:50–3:00**: Close: *"Detect, decide, act, and measure — one loop, five agents, real guardrails."*
