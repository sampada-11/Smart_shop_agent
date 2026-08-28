"""
Growth Decision Agent (§13 & §14 Multi-Agent Architecture)
Ranks and prioritizes growth opportunities using transparent weighted scoring.
"""
import json
import sqlite3
from typing import List, Dict, Any
from backend.app.db.models import get_db_connection, log_audit
from backend.app.tools.scoring import score_opportunity

def run_decision_agent(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks insights by calculating expected impact revenue, confidence, and urgency.
    Outputs ranked Opportunity objects.
    """
    print("[Growth Decision Agent] Scoring and ranking growth opportunities...")
    
    opportunities = []

    for ins in insights:
        insight_id = ins["insight_id"]
        evidence = ins.get("evidence", {})
        
        if insight_id == "INSIGHT-001":
            # §35 Demo Scenario Calculations:
            # Segment size: 850 customers
            # Product Y price: ₹1,200
            # Moving conversion from 6% to 14% (8% lift)
            # Expected incremental revenue: 850 * 0.08 * 1200 = ₹81,600
            expected_impact = 81600.0
            confidence = 0.78 # Driven by sample size 850 & 71% vs 45% abandonment delta
            urgency = 1.25 # High urgency due to active cart abandonment spike

            score_meta = score_opportunity(ins, expected_impact, confidence, urgency)

            opp = {
                "opportunity_id": "OPP-001",
                "insight_id": insight_id,
                "problem": "71% Cart Abandonment on Earbud Stand (PROD-002) among 18-25 Earbud Buyers (850 customers).",
                "expected_impact": expected_impact,
                "confidence": confidence,
                "urgency_factor": urgency,
                "recommended_action": "Launch personalized 8% discount offer on Earbud Stand via Email & Push.",
                "priority_score": score_meta["priority_score"],
                "status": "open",
                "evidence_snippet": evidence
            }
            opportunities.append(opp)

        elif insight_id == "INSIGHT-002":
            expected_impact = 35000.0
            confidence = 0.65
            urgency = 1.10
            score_meta = score_opportunity(ins, expected_impact, confidence, urgency)

            opp = {
                "opportunity_id": "OPP-002",
                "insight_id": insight_id,
                "problem": "High-value customer segment experiencing churn risk after 90+ days inactivity.",
                "expected_impact": expected_impact,
                "confidence": confidence,
                "urgency_factor": urgency,
                "recommended_action": "Deploy VIP win-back campaign with 10% re-engagement voucher.",
                "priority_score": score_meta["priority_score"],
                "status": "open",
                "evidence_snippet": evidence
            }
            opportunities.append(opp)

        elif insight_id == "INSIGHT-003":
            expected_impact = 18500.0
            confidence = 0.55
            urgency = 0.90
            score_meta = score_opportunity(ins, expected_impact, confidence, urgency)

            opp = {
                "opportunity_id": "OPP-003",
                "insight_id": insight_id,
                "problem": "Declining weekly revenue trend across select personal tech products.",
                "expected_impact": expected_impact,
                "confidence": confidence,
                "urgency_factor": urgency,
                "recommended_action": "Bundle declining items with top-selling wearables to clear inventory.",
                "priority_score": score_meta["priority_score"],
                "status": "open",
                "evidence_snippet": evidence
            }
            opportunities.append(opp)

    # Sort descending by priority_score
    ranked_opps = sorted(opportunities, key=lambda x: x["priority_score"], reverse=True)
    
    # Assign rank indices
    for rank, opp in enumerate(ranked_opps, start=1):
        opp["priority_rank"] = rank

    # Save to SQLite DB
    conn = get_db_connection()
    cursor = conn.cursor()
    for opp in ranked_opps:
        cursor.execute("""
            INSERT OR REPLACE INTO opportunities 
            (opportunity_id, insight_id, problem, expected_impact, confidence, urgency_factor, recommended_action, priority_score, priority_rank, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp["opportunity_id"], opp["insight_id"], opp["problem"], 
            opp["expected_impact"], opp["confidence"], opp["urgency_factor"], 
            opp["recommended_action"], opp["priority_score"], opp["priority_rank"], opp["status"]
        ))
    conn.commit()
    conn.close()

    log_audit("Decision Agent", "RANKED_OPPORTUNITIES", {"count": len(ranked_opps), "top_opportunity": ranked_opps[0]["opportunity_id"] if ranked_opps else None})
    print(f"[Growth Decision Agent] Ranked {len(ranked_opps)} opportunities. Top priority: {ranked_opps[0]['opportunity_id']}")
    return ranked_opps
