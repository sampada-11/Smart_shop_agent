"""
GrowthPilot (AI Commerce Growth Agent) - One-Click Application Launcher
"""
import os
import sys
import uvicorn

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.db.seed_synthetic_data import seed_database
from backend.app.agents.orchestrator import run_full_pipeline

def main():
    print("=" * 70)
    print("  GrowthPilot — Autonomous AI Commerce Growth Agent System  ")
    print("=" * 70)
    
    # 1. Database & Synthetic Dataset Initialization
    print("\n[Step 1/3] Initializing Database & 6-Month Synthetic Dataset...")
    seed_database(force=False)
    
    # 2. Multi-Agent Pipeline Run
    print("\n[Step 2/3] Executing Multi-Agent Analysis Pipeline...")
    state = run_full_pipeline()
    print(f"-> Insights Detected: {state['insights_count']}")
    print(f"-> Opportunities Ranked: {state['opportunities_count']}")
    if state.get("top_opportunity"):
        print(f"-> Top Opportunity Flagged: {state['top_opportunity']['opportunity_id']} - {state['top_opportunity']['problem']}")
    
    # 3. Launch Server & Dashboard
    print("\n[Step 3/3] Launching GrowthPilot Dashboard & FastAPI Backend...")
    print("-> Access Dashboard UI at: http://127.0.0.1:8000/")
    print("-> Interactive API Specs at: http://127.0.0.1:8000/docs")
    print("=" * 70 + "\n")
    
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
