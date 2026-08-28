"""
Deterministic Rule-Based Guardrails Tool (§23 & §24 Guardrails Design)
"""
from typing import Dict, Any, List, Tuple

MAX_DISCOUNT_CEILING = 15.0 # % max allowed discount
WEEKLY_BUDGET_CAP = 50000.0 # Maximum total weekly discount budget
MIN_SAMPLE_SIZE = 30 # Minimum evidence sample size required

def check_guardrails(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates rule-based guardrails against a proposed campaign before execution.
    Returns risk_tier ('Low', 'Medium', 'High', 'Blocked') and reasons list.
    """
    offer_pct = proposal.get("offer_pct", 0.0)
    target_segment = proposal.get("target_segment", "")
    segment_size = proposal.get("segment_size", 0)
    estimated_cost = proposal.get("estimated_cost", 0.0)
    sample_size = proposal.get("sample_size", MIN_SAMPLE_SIZE)

    reasons: List[str] = []
    is_blocked = False

    # 1. Sample Size Check
    if sample_size < MIN_SAMPLE_SIZE:
        reasons.append(f"Insufficient sample size: {sample_size} customers (minimum required is {MIN_SAMPLE_SIZE}).")
        is_blocked = True

    # 2. Excessive Discount Check
    if offer_pct > MAX_DISCOUNT_CEILING:
        reasons.append(f"Excessive discount requested: {offer_pct}% exceeds policy ceiling of {MAX_DISCOUNT_CEILING}%.")
        is_blocked = True

    # 3. Budget Limit Check
    if estimated_cost > WEEKLY_BUDGET_CAP:
        reasons.append(f"Estimated budget cost (${estimated_cost:,.2f}) exceeds weekly cap (${WEEKLY_BUDGET_CAP:,.2f}).")
        is_blocked = True

    if is_blocked:
        return {
            "risk_tier": "High",
            "status": "Blocked",
            "reasons": reasons,
            "can_auto_execute": False,
            "requires_approval": True,
            "requires_justification": True
        }

    # Determine Risk Tier according to §23
    # Low: Internal alert / feature only
    # Medium: Discount <= 10%, segment size <= 1000
    # High: Discount > 10% or segment size > 1000
    if offer_pct <= 10.0 and segment_size <= 1000:
        risk_tier = "Medium"
        reasons.append("Medium risk: Discount ≤ 10% targeting ≤ 1,000 customers. Requires 1-click approval.")
        requires_justification = False
    else:
        risk_tier = "High"
        reasons.append("High risk: Action exceeds medium thresholds. Requires human approval with explicit justification.")
        requires_justification = True

    return {
        "risk_tier": risk_tier,
        "status": "Needs Approval",
        "reasons": reasons,
        "can_auto_execute": False,
        "requires_approval": True,
        "requires_justification": requires_justification
    }
