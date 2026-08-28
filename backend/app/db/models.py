"""
Database Models & SQLite Schema for GrowthPilot
"""
import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "growthpilot.db")


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates SQLite database tables according to §18 ER Diagram."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        age INTEGER,
        segment TEXT,
        channel TEXT,
        signup_date TEXT
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        name TEXT,
        category TEXT,
        base_price REAL,
        launch_date TEXT
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id TEXT PRIMARY KEY,
        customer_id TEXT,
        product_id TEXT,
        purchase_date TEXT,
        quantity INTEGER,
        discount_pct REAL,
        revenue REAL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        customer_id TEXT,
        start_time TEXT,
        channel TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS cart_events (
        cart_event_id TEXT PRIMARY KEY,
        session_id TEXT,
        customer_id TEXT,
        product_id TEXT,
        event_type TEXT,
        event_time TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    CREATE TABLE IF NOT EXISTS insights (
        insight_id TEXT PRIMARY KEY,
        type TEXT,
        description TEXT,
        evidence TEXT, -- JSON string
        generated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS opportunities (
        opportunity_id TEXT PRIMARY KEY,
        insight_id TEXT,
        problem TEXT,
        expected_impact REAL,
        confidence REAL,
        urgency_factor REAL DEFAULT 1.0,
        recommended_action TEXT,
        priority_score REAL,
        priority_rank INTEGER,
        status TEXT DEFAULT 'open',
        FOREIGN KEY (insight_id) REFERENCES insights(insight_id)
    );

    CREATE TABLE IF NOT EXISTS campaign_proposals (
        campaign_id TEXT PRIMARY KEY,
        opportunity_id TEXT,
        target_segment TEXT,
        product_id TEXT,
        offer_pct REAL,
        channel TEXT,
        generated_copy TEXT,
        expected_roi REAL,
        risk_tier TEXT,
        risk_reasons TEXT, -- JSON string
        status TEXT DEFAULT 'drafted',
        created_at TEXT,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(opportunity_id)
    );

    CREATE TABLE IF NOT EXISTS campaign_interactions (
        interaction_id TEXT PRIMARY KEY,
        campaign_id TEXT,
        customer_id TEXT,
        interaction_type TEXT,
        interaction_time TEXT,
        FOREIGN KEY (campaign_id) REFERENCES campaign_proposals(campaign_id),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS executions (
        execution_id TEXT PRIMARY KEY,
        campaign_id TEXT,
        approved_by TEXT,
        justification TEXT,
        executed_at TEXT,
        mock_api_status TEXT,
        execution_token TEXT,
        FOREIGN KEY (campaign_id) REFERENCES campaign_proposals(campaign_id)
    );

    CREATE TABLE IF NOT EXISTS experiment_results (
        result_id TEXT PRIMARY KEY,
        execution_id TEXT,
        expected_conversion REAL,
        actual_conversion REAL,
        expected_revenue REAL,
        actual_revenue REAL,
        verdict TEXT,
        ai_reasoning TEXT,
        evaluated_at TEXT,
        FOREIGN KEY (execution_id) REFERENCES executions(execution_id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id TEXT PRIMARY KEY,
        timestamp TEXT,
        agent_or_user TEXT,
        action_type TEXT,
        details TEXT -- JSON string
    );
    """)

    conn.commit()
    conn.close()


def log_audit(agent_or_user: str, action_type: str, details: Dict[str, Any]):
    """Logs an agent decision or human action into the audit trail."""
    conn = get_db_connection()
    cursor = conn.cursor()
    log_id = f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    cursor.execute("""
        INSERT INTO audit_logs (log_id, timestamp, agent_or_user, action_type, details)
        VALUES (?, ?, ?, ?, ?)
    """, (log_id, datetime.now().isoformat(), agent_or_user, action_type, json.dumps(details)))
    conn.commit()
    conn.close()
