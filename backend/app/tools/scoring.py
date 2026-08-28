"""
Opportunity Scoring & Ranking Tool (§22 Agent Decision-Making Logic)
"""
from typing import Dict, Any

def score_opportunity(
    insight: Dict[str, Any],
    expected_impact_revenue: float,
    confidence: float,
    urgency_factor: float = 1.0
) -> Dict[str, Any]:
    """
    Computes priority_score according to transparent formula:
    priority_score = expected_impact_revenue * confidence * urgency_factor
    """
    confidence_clamped = min(max(confidence, 0.0), 1.0)
    priority_score = round(expected_impact_revenue * confidence_clamped * urgency_factor, 2)
    
    return {
        "expected_impact_revenue": round(expected_impact_revenue, 2),
        "confidence": confidence_clamped,
        "urgency_factor": urgency_factor,
        "priority_score": priority_score
    }
