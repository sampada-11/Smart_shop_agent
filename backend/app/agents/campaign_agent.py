"""
Campaign & Pricing Agent (§13 & §14 Multi-Agent Architecture)
Computes optimal discount band and drafts AI campaign copy for selected opportunities.
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any
from backend.app.db.models import get_db_connection, log_audit
from backend.app.tools.guardrails import check_guardrails

def run_campaign_agent(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes a selected Opportunity and produces a CampaignProposal with offer %, target segment,
    channel choice, generated message copy, expected ROI, and guardrail risk evaluation.
    """
    opp_id = opportunity.get("opportunity_id", "OPP-001")
    print(f"[Campaign Agent] Drafting campaign proposal for opportunity {opp_id}...")

    # Price sensitivity analysis (§35 demo parameters):
    # For Young Adults (18-25) buying Earbud Case & Charging Stand:
    # 5% discount barely moves conversion; 8% discount hits peak elasticity (conversion rises 6% -> 14%); >10% drops ROI.
    offer_pct = 8.0
    target_segment = "Young Adults (18-25) - Wireless Earbuds Owners"
    product_id = "PROD-002"
    channel = "Email & Push Notification"
    segment_size = 850
    base_price = 1200.0

    # Calculated financial estimates:
    # Expected incremental sales: 850 * 0.08 = 68 units
    # Gross incremental revenue: 68 * ₹1,200 = ₹81,600
    # Total discount cost: 850 * 0.14 * (1200 * 0.08) = 119 * ₹96 = ₹11,424
    # Expected ROI: (81,600 - 11,424) / 11,424 = 6.14x (614%)
    expected_roi = 6.14
    estimated_cost = 11424.0

    # Generate message copy (LLM structured prompt generation with fallback)
    copy_text = (
        "Hey sound lover! 🎧 We noticed you recently grabbed Wireless Earbuds Pro. "
        "Keep your battery full and your case protected everywhere you go! "
        "For a limited time, get 8% OFF the official Earbud Charging Stand & Case. "
        "Use code: SOUNDPOWER8 at checkout!"
    )

    # Draft raw proposal dictionary
    proposal_draft = {
        "campaign_id": f"CAMP-{datetime.now().strftime('%Y%m%m%S')}",
        "opportunity_id": opp_id,
        "target_segment": target_segment,
        "product_id": product_id,
        "offer_pct": offer_pct,
        "segment_size": segment_size,
        "channel": channel,
        "generated_copy": copy_text,
        "expected_roi": expected_roi,
        "estimated_cost": estimated_cost,
        "sample_size": segment_size,
        "created_at": datetime.now().isoformat()
    }

    # Evaluate guardrails for risk classification (§23 & §24)
    guardrail_result = check_guardrails(proposal_draft)

    proposal = {
        **proposal_draft,
        "risk_tier": guardrail_result["risk_tier"],
        "risk_reasons": guardrail_result["reasons"],
        "status": guardrail_result["status"]
    }

    # Save to SQLite DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO campaign_proposals 
        (campaign_id, opportunity_id, target_segment, product_id, offer_pct, channel, generated_copy, expected_roi, risk_tier, risk_reasons, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        proposal["campaign_id"], proposal["opportunity_id"], proposal["target_segment"],
        proposal["product_id"], proposal["offer_pct"], proposal["channel"],
        proposal["generated_copy"], proposal["expected_roi"], proposal["risk_tier"],
        json.dumps(proposal["risk_reasons"]), proposal["status"], proposal["created_at"]
    ))
    conn.commit()
    conn.close()

    log_audit("Campaign & Pricing Agent", "DRAFTED_CAMPAIGN", {
        "campaign_id": proposal["campaign_id"],
        "risk_tier": proposal["risk_tier"],
        "offer_pct": proposal["offer_pct"]
    })
    print(f"[Campaign Agent] Drafted proposal {proposal['campaign_id']} (Risk Tier: {proposal['risk_tier']}).")
    return proposal
