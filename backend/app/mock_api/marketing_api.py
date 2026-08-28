"""
Mock Marketing API Platform (§19 & §24 Security Design)
Simulates external email/push marketing execution service.
Requires valid execution_token minted after guardrail + approval pass.
"""
from datetime import datetime
from typing import Dict, Any

def execute_campaign_mock_api(proposal: Dict[str, Any], execution_token: str) -> Dict[str, Any]:
    """
    Simulates sending campaign messages via mock marketing API (Klaviyo / Meta Ads / Push Service).
    Validates token and returns execution receipt.
    """
    if not execution_token or not execution_token.startswith("TOKEN-EXEC-"):
        return {
            "status": "FAILED",
            "error": "UnauthorizedAction: Invalid or missing execution_token.",
            "recipients_reached": 0
        }

    campaign_id = proposal.get("campaign_id", "CAMP-UNKNOWN")
    target_segment = proposal.get("target_segment", "Default Segment")
    segment_size = proposal.get("segment_size", 850)
    channel = proposal.get("channel", "Email & Push Notification")
    offer_pct = proposal.get("offer_pct", 8.0)

    receipt = {
        "status": "SENT",
        "mock_provider": "GrowthPilot Mock Marketing Gateway v1.0",
        "campaign_id": campaign_id,
        "target_segment": target_segment,
        "channel": channel,
        "offer_pct": offer_pct,
        "recipients_reached": segment_size,
        "delivered_count": int(segment_size * 0.98), # 98% delivery rate
        "open_rate_pct": 42.5,
        "execution_token_used": execution_token,
        "dispatched_at": datetime.now().isoformat()
    }

    print(f"[Mock Marketing API] Executed campaign {campaign_id} to {segment_size} recipients via {channel}.")
    return receipt
