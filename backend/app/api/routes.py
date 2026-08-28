"""
FastAPI REST API Routes (§Appendix F Endpoint List)
"""
import json
import sqlite3
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from backend.app.db.models import get_db_connection
from backend.app.tools.segmentation import compute_customer_segmentation
from backend.app.tools.churn import compute_churn_risk_list
from backend.app.tools.trend import compute_product_trends
from backend.app.agents.orchestrator import run_full_pipeline, approve_and_execute_campaign
from backend.app.agents.campaign_agent import run_campaign_agent

router = APIRouter(prefix="/api")


class ApprovalRequest(BaseModel):
    approved_by: str = "Growth Manager"
    justification: Optional[str] = None


@router.get("/overview")
def get_executive_overview():
    """Executive Overview: revenue trend, conversion rate trend, top 3 growth opportunities, active alerts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculate overall metrics
    cursor.execute("SELECT COALESCE(SUM(revenue), 0), COUNT(order_item_id) FROM order_items")
    row = cursor.fetchone()
    total_revenue = float(row[0])
    total_orders = int(row[1])

    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]

    conversion_rate = round((total_orders / (total_sessions + 1e-5)) * 100, 2)

    # Fetch top opportunities
    cursor.execute("SELECT * FROM opportunities ORDER BY priority_rank ASC LIMIT 3")
    opp_rows = cursor.fetchall()
    top_opportunities = [dict(r) for r in opp_rows]

    conn.close()

    return {
        "headline_metrics": {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_sessions": total_sessions,
            "conversion_rate_pct": conversion_rate,
            "active_alerts_count": 2
        },
        "top_opportunities": top_opportunities,
        "ai_weekly_recommendation": (
            "Primary Growth Focus: 71% Cart Abandonment on Earbud Stand (PROD-002) among 18-25 Earbud Buyers. "
            "Launching an 8% targeted discount offers ₹81,600 expected revenue lift."
        )
    }


@router.get("/customers/segments")
def get_customer_segments():
    """Returns customer segment breakdown and RFM analytics."""
    return compute_customer_segmentation()


@router.get("/customers/churn-risk")
def get_churn_risk_list(limit: int = Query(20, ge=1, le=100)):
    """Returns high churn risk customer list with scores."""
    return compute_churn_risk_list(limit=limit)


@router.get("/products/trends")
def get_product_trends():
    """Returns product growth/decline trends and category distribution."""
    return compute_product_trends()


@router.get("/opportunities")
def get_opportunities():
    """Returns ranked growth opportunities."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opportunities ORDER BY priority_rank ASC")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        d = dict(r)
        result.append(d)
    return result


@router.get("/opportunities/{id}")
def get_opportunity_detail(id: str):
    """Returns detail & evidence for a specific opportunity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, i.type AS insight_type, i.description AS insight_desc, i.evidence 
        FROM opportunities o
        JOIN insights i ON o.insight_id = i.insight_id
        WHERE o.opportunity_id = ?
    """, (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    data = dict(row)
    if data.get("evidence"):
        try:
            data["evidence"] = json.loads(data["evidence"])
        except Exception:
            pass
    return data


@router.post("/opportunities/{id}/campaign")
def draft_campaign_for_opportunity(id: str):
    """Triggers Campaign Agent to draft a campaign proposal for an opportunity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opportunities WHERE opportunity_id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp = dict(row)
    proposal = run_campaign_agent(opp)
    return proposal


@router.get("/campaigns/{id}")
def get_campaign_detail(id: str):
    """Returns details for a drafted campaign proposal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_proposals WHERE campaign_id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Campaign proposal not found")

    data = dict(row)
    if data.get("risk_reasons"):
        try:
            data["risk_reasons"] = json.loads(data["risk_reasons"])
        except Exception:
            pass
    return data


@router.post("/campaigns/{id}/approve")
def approve_campaign_proposal(id: str, payload: ApprovalRequest = Body(...)):
    """Human approval endpoint for medium/high risk campaign proposals."""
    try:
        result = approve_and_execute_campaign(
            campaign_id=id,
            approved_by=payload.approved_by,
            justification=payload.justification
        )
        return result
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/campaigns/{id}/execute")
def execute_campaign_endpoint(id: str, payload: ApprovalRequest = Body(...)):
    """Execute campaign proposal (alias to approve and execute)."""
    return approve_campaign_proposal(id=id, payload=payload)


@router.get("/experiments/{id}")
def get_experiment_detail(id: str):
    """Returns post-campaign experiment result details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT er.*, e.campaign_id, e.approved_by, e.executed_at, c.target_segment, c.offer_pct
        FROM experiment_results er
        JOIN executions e ON er.execution_id = e.execution_id
        JOIN campaign_proposals c ON e.campaign_id = c.campaign_id
        WHERE er.result_id = ? OR er.execution_id = ? OR e.campaign_id = ?
    """, (id, id, id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Experiment result not found")

    return dict(row)


@router.get("/audit-log")
def get_audit_log(limit: int = Query(50, ge=1, le=200)):
    """Returns full audit log trail of agent decisions and human approvals."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        d = dict(r)
        if d.get("details"):
            try:
                d["details"] = json.loads(d["details"])
            except Exception:
                pass
        logs.append(d)
    return logs


@router.post("/pipeline/run")
def trigger_full_pipeline():
    """Triggers the full multi-agent detection and decision loop."""
    return run_full_pipeline()
