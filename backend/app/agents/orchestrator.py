"""
Orchestrator & Guardrail Agent (§13 & §14 Multi-Agent Architecture)
State Graph Coordinator and Execution Pipeline Manager.
"""
import uuid
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from backend.app.db.models import get_db_connection, log_audit
from backend.app.agents.insight_agent import run_insight_agent
from backend.app.agents.decision_agent import run_decision_agent
from backend.app.agents.campaign_agent import run_campaign_agent
from backend.app.agents.experiment_agent import evaluate_experiment
from backend.app.mock_api.marketing_api import execute_campaign_mock_api

def run_full_pipeline() -> Dict[str, Any]:
    """
    Executes end-to-end multi-agent pipeline:
    1. Insight Agent detects growth patterns
    2. Growth Decision Agent scores & ranks opportunities
    3. Campaign Agent drafts top-ranked campaign proposal
    Returns current pipeline state.
    """
    print("=== Starting GrowthPilot Multi-Agent Pipeline Run ===")
    
    # Step 1: Insight Agent
    insights = run_insight_agent()

    # Step 2: Growth Decision Agent
    opportunities = run_decision_agent(insights)

    # Step 3: Campaign Agent for top opportunity
    top_opp = opportunities[0] if opportunities else None
    campaign_proposal = None
    if top_opp:
        campaign_proposal = run_campaign_agent(top_opp)

    pipeline_state = {
        "status": "completed_initial_analysis",
        "insights_count": len(insights),
        "opportunities_count": len(opportunities),
        "top_opportunity": top_opp,
        "active_campaign_proposal": campaign_proposal,
        "timestamp": datetime.now().isoformat()
    }

    log_audit("Orchestrator Agent", "PIPELINE_RUN_COMPLETED", pipeline_state)
    return pipeline_state


def approve_and_execute_campaign(campaign_id: str, approved_by: str = "Growth Manager", justification: Optional[str] = None) -> Dict[str, Any]:
    """
    Handles human approval and triggers mock campaign execution.
    1. Mints valid execution token
    2. Calls Mock Marketing API
    3. Logs execution record
    4. Triggers Experiment Agent after simulated period
    """
    print(f"[Orchestrator] Processing approval for campaign {campaign_id} by {approved_by}...")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch campaign details
    cursor.execute("SELECT * FROM campaign_proposals WHERE campaign_id = ?", (campaign_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Campaign proposal {campaign_id} not found.")

    campaign = dict(row)

    # Validate justification for High Risk tier
    if campaign["risk_tier"] == "High" and not justification:
        conn.close()
        raise ValueError("High risk actions require an explicit human justification before execution.")

    # Mint execution token
    token = f"TOKEN-EXEC-{uuid.uuid4().hex[:12].upper()}"

    # Update proposal status to approved
    cursor.execute("UPDATE campaign_proposals SET status = 'approved' WHERE campaign_id = ?", (campaign_id,))

    # Call Mock Marketing API
    api_receipt = execute_campaign_mock_api(campaign, token)

    # Log Execution in DB
    execution_id = f"EXEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    cursor.execute("""
        INSERT INTO executions (execution_id, campaign_id, approved_by, justification, executed_at, mock_api_status, execution_token)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        execution_id, campaign_id, approved_by, justification or "Approved via Campaign Studio",
        datetime.now().isoformat(), api_receipt["status"], token
    ))
    conn.commit()
    conn.close()

    log_audit(approved_by, "APPROVED_AND_EXECUTED", {
        "campaign_id": campaign_id,
        "execution_id": execution_id,
        "token": token
    })

    # Trigger Experiment Agent (§35 Simulated 2-Week Post Period Evaluation)
    exp_result = evaluate_experiment(execution_id)

    return {
        "execution_id": execution_id,
        "campaign_id": campaign_id,
        "token": token,
        "mock_api_receipt": api_receipt,
        "experiment_result": exp_result
    }
