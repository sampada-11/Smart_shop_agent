"""
GrowthPilot Unit & Integration Test Suite
"""
import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.models import init_db, get_db_connection
from backend.app.db.seed_synthetic_data import seed_database
from backend.app.tools.segmentation import compute_customer_segmentation
from backend.app.tools.churn import compute_churn_risk_list
from backend.app.tools.trend import compute_product_trends
from backend.app.tools.scoring import score_opportunity
from backend.app.tools.guardrails import check_guardrails
from backend.app.agents.insight_agent import run_insight_agent
from backend.app.agents.decision_agent import run_decision_agent
from backend.app.agents.campaign_agent import run_campaign_agent
from backend.app.agents.experiment_agent import evaluate_experiment
from backend.app.agents.orchestrator import run_full_pipeline, approve_and_execute_campaign


class TestGrowthPilotToolsAndAgents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seeds the test database before running tests."""
        init_db()
        seed_database(force=False)

    def test_01_segmentation_tool(self):
        """Verifies customer segmentation tool returns valid segments and total count."""
        result = compute_customer_segmentation()
        self.assertIn("segments", result)
        self.assertGreater(result["total_customers"], 0)
        self.assertGreater(len(result["segments"]), 0)

    def test_02_churn_tool(self):
        """Verifies churn risk tool returns customer churn scores between 0 and 1."""
        high_risk_list = compute_churn_risk_list(limit=10)
        self.assertIsInstance(high_risk_list, list)
        self.assertGreater(len(high_risk_list), 0)
        for c in high_risk_list:
            self.assertGreaterEqual(c["churn_risk_score"], 0.0)
            self.assertLessEqual(c["churn_risk_score"], 1.0)

    def test_03_trend_tool(self):
        """Verifies product trend analysis computes growth rates and categories."""
        result = compute_product_trends()
        self.assertIn("products", result)
        self.assertIn("categories", result)
        self.assertGreater(len(result["products"]), 0)

    def test_04_scoring_formula(self):
        """Verifies transparent priority_score formula: impact * confidence * urgency."""
        insight = {"insight_id": "TEST-01"}
        score_data = score_opportunity(insight, expected_impact_revenue=10000.0, confidence=0.8, urgency_factor=1.5)
        self.assertEqual(score_data["priority_score"], 12000.0)

    def test_05_guardrails(self):
        """Verifies rule-based guardrails block excessive discount (>15%) and enforce sample size."""
        # Excessive discount test
        high_disc_proposal = {"offer_pct": 20.0, "segment_size": 100, "estimated_cost": 1000.0, "sample_size": 50}
        res_high_disc = check_guardrails(high_disc_proposal)
        self.assertEqual(res_high_disc["status"], "Blocked")
        self.assertTrue(res_high_disc["requires_approval"])

        # Low sample size test
        small_sample_proposal = {"offer_pct": 8.0, "segment_size": 10, "estimated_cost": 500.0, "sample_size": 15}
        res_small_sample = check_guardrails(small_sample_proposal)
        self.assertEqual(res_small_sample["status"], "Blocked")

        # Medium risk valid proposal test
        valid_proposal = {"offer_pct": 8.0, "segment_size": 850, "estimated_cost": 11424.0, "sample_size": 850}
        res_valid = check_guardrails(valid_proposal)
        self.assertEqual(res_valid["risk_tier"], "Medium")

    def test_06_full_agent_pipeline(self):
        """Verifies full multi-agent pipeline run and top opportunity generation."""
        state = run_full_pipeline()
        self.assertEqual(state["status"], "completed_initial_analysis")
        self.assertGreater(state["insights_count"], 0)
        self.assertGreater(state["opportunities_count"], 0)
        self.assertIsNotNone(state["top_opportunity"])

    def test_07_approval_and_mock_execution(self):
        """Verifies human approval and mock marketing API execution receipt generation."""
        state = run_full_pipeline()
        proposal = state["active_campaign_proposal"]
        self.assertIsNotNone(proposal)
        campaign_id = proposal["campaign_id"]
        
        # Approve campaign
        exec_res = approve_and_execute_campaign(campaign_id, approved_by="Test Growth Manager", justification="Testing approval pipeline")
        self.assertIn("execution_id", exec_res)
        self.assertEqual(exec_res["mock_api_receipt"]["status"], "SENT")
        self.assertEqual(exec_res["experiment_result"]["verdict"], "Campaign Succeeded")


if __name__ == "__main__":
    unittest.main()
