"""
Churn Risk Calculation Tool (§21 AI/ML Component)
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from backend.app.db.models import get_db_connection

def compute_churn_risk_list(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Computes churn probability score for each customer using recency, order drop, and session activity.
    Returns high churn risk customer list.
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            c.customer_id,
            c.age,
            c.segment,
            c.channel,
            COUNT(DISTINCT o.order_item_id) AS total_orders,
            COALESCE(SUM(o.revenue), 0) AS total_spent,
            MAX(o.purchase_date) AS last_order_date,
            COUNT(DISTINCT s.session_id) AS total_sessions,
            MAX(s.start_time) AS last_session_date
        FROM customers c
        LEFT JOIN order_items o ON c.customer_id = o.customer_id
        LEFT JOIN sessions s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return []

    # Dates parsing
    max_order_dt = pd.to_datetime(df["last_order_date"]).max() if not df["last_order_date"].isna().all() else pd.to_datetime("now")
    df["last_order_dt"] = pd.to_datetime(df["last_order_date"])
    df["last_session_dt"] = pd.to_datetime(df["last_session_date"])

    df["days_since_order"] = (max_order_dt - df["last_order_dt"]).dt.days.fillna(180)
    df["days_since_session"] = (max_order_dt - df["last_session_dt"]).dt.days.fillna(180)

    # Churn probability model score:
    # High recency days + low order frequency + session inactivity => high churn risk score (0 to 1)
    recency_factor = np.clip(df["days_since_order"] / 120.0, 0, 1.0)
    session_factor = np.clip(df["days_since_session"] / 90.0, 0, 1.0)
    order_freq_factor = np.clip(1.0 - (df["total_orders"] / 10.0), 0, 1.0)

    # Hybrid weighted churn score
    df["churn_risk_score"] = (0.50 * recency_factor + 0.30 * session_factor + 0.20 * order_freq_factor).round(3)
    df["conversion_propensity"] = (1.0 - df["churn_risk_score"]).round(3)

    # Filter high churn risk candidates
    high_risk_df = df.sort_values(by="churn_risk_score", ascending=False).head(limit)

    results = []
    for _, row in high_risk_df.iterrows():
        results.append({
            "customer_id": row["customer_id"],
            "age": int(row["age"]),
            "segment": row["segment"],
            "channel": row["channel"],
            "total_orders": int(row["total_orders"]),
            "total_spent": round(float(row["total_spent"]), 2),
            "days_since_last_order": int(row["days_since_order"]),
            "churn_risk_score": float(row["churn_risk_score"]),
            "conversion_propensity": float(row["conversion_propensity"])
        })

    return results
