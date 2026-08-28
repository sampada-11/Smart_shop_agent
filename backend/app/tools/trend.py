"""
Product Trend & Category Analytics Tool (§21 AI/ML Component)
"""
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from backend.app.db.models import get_db_connection

def compute_product_trends() -> Dict[str, Any]:
    """
    Computes product growth/decline rates and category trends using rolling window revenue slopes.
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            p.product_id,
            p.name,
            p.category,
            p.base_price,
            o.purchase_date,
            o.quantity,
            o.revenue
        FROM products p
        JOIN order_items o ON p.product_id = o.product_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return {"products": [], "categories": []}

    df["purchase_date"] = pd.to_datetime(df["purchase_date"])
    df["week"] = df["purchase_date"].dt.to_period("W").dt.to_timestamp()

    # Product level slope computation
    product_stats = []
    for (pid, pname, cat, base_price), group in df.groupby(["product_id", "name", "category", "base_price"]):
        weekly_rev = group.groupby("week")["revenue"].sum().reset_index().sort_values("week")
        
        total_rev = float(group["revenue"].sum())
        total_units = int(group["quantity"].sum())

        if len(weekly_rev) >= 2:
            x = np.arange(len(weekly_rev))
            y = weekly_rev["revenue"].values
            slope, _ = np.polyfit(x, y, 1)
            growth_rate = round(float(slope / (y.mean() + 1e-5)) * 100, 2)
        else:
            growth_rate = 0.0

        if growth_rate > 5.0:
            trend_label = "Rising"
        elif growth_rate < -5.0:
            trend_label = "Declining"
        else:
            trend_label = "Stable"

        product_stats.append({
            "product_id": pid,
            "name": pname,
            "category": cat,
            "base_price": float(base_price),
            "total_revenue": round(total_rev, 2),
            "total_units_sold": total_units,
            "growth_rate_pct": growth_rate,
            "trend_label": trend_label
        })

    # Category level aggregation
    cat_summary = df.groupby("category").agg(
        total_revenue=("revenue", "sum"),
        total_units=("quantity", "sum"),
        product_count=("product_id", "nunique")
    ).reset_index()

    categories = []
    for _, row in cat_summary.iterrows():
        categories.append({
            "category": row["category"],
            "total_revenue": round(float(row["total_revenue"]), 2),
            "total_units": int(row["total_units"]),
            "product_count": int(row["product_count"])
        })

    return {
        "products": sorted(product_stats, key=lambda x: x["total_revenue"], reverse=True),
        "categories": categories
    }
