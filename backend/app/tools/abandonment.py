"""
Cart Abandonment & Conversion Bottleneck Tool (§14 & §20 Function Calling Design)
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Any
from backend.app.db.models import get_db_connection

def compute_cart_abandonment_stats() -> List[Dict[str, Any]]:
    """
    Computes cart abandonment rate and conversion rates by customer segment and product pair.
    Flags segments with abnormal abandonment (>50%).
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            ce.cart_event_id,
            ce.session_id,
            ce.customer_id,
            ce.product_id,
            p.name AS product_name,
            p.base_price,
            c.age,
            c.segment,
            ce.event_type
        FROM cart_events ce
        JOIN customers c ON ce.customer_id = c.customer_id
        JOIN products p ON ce.product_id = p.product_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return []

    # Group by segment and product to calculate add-to-cart vs. abandon vs. checkout
    abandonment_results = []
    
    for (seg, pid, pname, price), group in df.groupby(["segment", "product_id", "product_name", "base_price"]):
        total_carts = len(group[group["event_type"] == "add_to_cart"])
        abandoned_carts = len(group[group["event_type"] == "abandon"])
        checkouts = len(group[group["event_type"] == "checkout"])
        
        if total_carts == 0:
            continue

        abandon_rate = round(float(abandoned_carts / total_carts), 3)
        conversion_rate = round(float(checkouts / total_carts), 3)
        customer_count = group["customer_id"].nunique()

        abandonment_results.append({
            "segment": seg,
            "product_id": pid,
            "product_name": pname,
            "base_price": float(price),
            "customer_count": int(customer_count),
            "total_carts": int(total_carts),
            "abandoned_carts": int(abandoned_carts),
            "checkouts": int(checkouts),
            "abandonment_rate": abandon_rate,
            "conversion_rate": conversion_rate,
            "abnormal": abandon_rate > 0.50
        })

    return sorted(abandonment_results, key=lambda x: (x["abnormal"], x["abandonment_rate"]), reverse=True)
