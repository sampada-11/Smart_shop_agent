"""
RFM Customer Segmentation & CLV Estimation Tool (§21 AI/ML Component)
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.app.db.models import get_db_connection

def compute_customer_segmentation() -> Dict[str, Any]:
    """
    Computes RFM (Recency, Frequency, Monetary) scores and segment groupings.
    Also estimates Customer Lifetime Value (CLV = historical avg order value * estimated 12-month purchase freq).
    """
    conn = get_db_connection()
    
    # Query customer purchase history
    query = """
        SELECT 
            c.customer_id,
            c.age,
            c.segment AS raw_segment,
            c.channel,
            COUNT(o.order_item_id) AS frequency,
            COALESCE(SUM(o.revenue), 0) AS total_monetary,
            COALESCE(AVG(o.revenue), 0) AS avg_order_value,
            MAX(o.purchase_date) AS last_purchase_date
        FROM customers c
        LEFT JOIN order_items o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return {"segments": [], "summary": {}}

    # Calculate recency in days
    now = datetime.now()
    df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"])
    max_date = df["last_purchase_date"].max() if not df["last_purchase_date"].isna().all() else now
    df["recency_days"] = (max_date - df["last_purchase_date"]).dt.days.fillna(180)

    # Compute CLV estimate: historical avg order value * predicted annual frequency
    df["predicted_annual_freq"] = np.clip(df["frequency"] * 2.0, 1.0, 24.0)
    df["clv_estimate"] = (df["avg_order_value"] * df["predicted_annual_freq"]).round(2)

    # Segment summary breakdown
    segment_counts = df.groupby("raw_segment").agg(
        customer_count=("customer_id", "count"),
        avg_clv=("clv_estimate", "mean"),
        avg_recency=("recency_days", "mean"),
        avg_monetary=("total_monetary", "mean"),
        total_revenue=("total_monetary", "sum")
    ).reset_index()

    segment_list = []
    for _, row in segment_counts.iterrows():
        segment_list.append({
            "segment_name": row["raw_segment"],
            "customer_count": int(row["customer_count"]),
            "avg_clv": round(float(row["avg_clv"]), 2),
            "avg_recency_days": round(float(row["avg_recency"]), 1),
            "avg_monetary": round(float(row["avg_monetary"]), 2),
            "total_revenue": round(float(row["total_revenue"]), 2)
        })

    return {
        "segments": segment_list,
        "total_customers": len(df),
        "avg_clv_overall": round(float(df["clv_estimate"].mean()), 2)
    }
