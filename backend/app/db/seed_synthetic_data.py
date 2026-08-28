"""
Synthetic E-Commerce Data Generator & Database Seeder for GrowthPilot (§35 Demo Scenario)
"""
import os
import random
import uuid
import pandas as pd
from datetime import datetime, timedelta
from backend.app.db.models import init_db, get_db_connection, log_audit

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "synthetic_ecommerce_dataset.csv")

def seed_database(force: bool = False):
    """Seeds synthetic 6-month e-commerce data with the §35 demo opportunity pattern."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] > 0 and not force:
        print("Database already seeded. Skipping seed process.")
        conn.close()
        return

    print("Generating synthetic 6-month dataset (~12,000 customers, 40 products, ~65,000 orders)...")
    random.seed(42)

    # 1. Generate Products (40 products)
    categories = ["Audio", "Wearables", "Accessories", "Smart Home", "Personal Tech"]
    products = [
        {"product_id": "PROD-001", "name": "Wireless Earbuds Pro", "category": "Audio", "base_price": 2999.0},
        {"product_id": "PROD-002", "name": "Earbud Case & Charging Stand", "category": "Audio", "base_price": 1200.0},
        {"product_id": "PROD-003", "name": "Active Noise Canceling Headphones", "category": "Audio", "base_price": 4999.0},
        {"product_id": "PROD-004", "name": "Bluetooth Speaker Mini", "category": "Audio", "base_price": 1499.0},
        {"product_id": "PROD-005", "name": "Smart Fitness Watch", "category": "Wearables", "base_price": 3499.0},
        {"product_id": "PROD-006", "name": "Smart Band Fitness Tracker", "category": "Wearables", "base_price": 1999.0},
        {"product_id": "PROD-007", "name": "Fast Wireless Charger Pad", "category": "Accessories", "base_price": 899.0},
        {"product_id": "PROD-008", "name": "USB-C Braided Cable Pack", "category": "Accessories", "base_price": 499.0},
        {"product_id": "PROD-009", "name": "Smart LED Bulb Pair", "category": "Smart Home", "base_price": 1299.0},
        {"product_id": "PROD-0010", "name": "Portable Power Bank 20000mAh", "category": "Personal Tech", "base_price": 1799.0},
    ]

    # Add remaining products to hit 40 products
    for i in range(11, 41):
        cat = categories[i % len(categories)]
        products.append({
            "product_id": f"PROD-{i:03d}",
            "name": f"Tech Gadget {cat} {i}",
            "category": cat,
            "base_price": round(random.uniform(499.0, 5999.0), 2)
        })

    cursor.executemany("""
        INSERT OR REPLACE INTO products (product_id, name, category, base_price, launch_date)
        VALUES (:product_id, :name, :category, :base_price, '2025-01-01')
    """, products)

    # 2. Generate Customers (12,000 customers)
    num_customers = 12000
    channels = ["Direct", "Google Search", "Instagram Ads", "Email Newsletter", "Affiliate"]
    
    customers = []
    earbud_buyers_18_25 = []

    start_date = datetime.now() - timedelta(days=180)

    for i in range(1, num_customers + 1):
        c_id = f"CUST-{i:05d}"
        age = random.randint(18, 65)
        channel = random.choice(channels)
        
        # Classify baseline segment
        if age <= 25:
            segment = "Young Adults (18-25)"
        elif age <= 40:
            segment = "Tech Enthusiasts (26-40)"
        else:
            segment = "Value Seekers (41+)"

        signup_dt = start_date + timedelta(days=random.randint(0, 90))
        customers.append((c_id, age, segment, channel, signup_dt.strftime("%Y-%m-%d")))

        # Track the specific 850 customers for §35 demo pattern
        if 18 <= age <= 25 and len(earbud_buyers_18_25) < 850:
            earbud_buyers_18_25.append(c_id)

    cursor.executemany("""
        INSERT OR REPLACE INTO customers (customer_id, age, segment, channel, signup_date)
        VALUES (?, ?, ?, ?, ?)
    """, customers)

    # 3. Generate Sessions, Cart Events, and Order Items
    order_items = []
    sessions = []
    cart_events = []
    csv_rows = []

    order_count = 0
    session_count = 0

    # Ensure the 850 customers in target segment have bought PROD-001 ("Wireless Earbuds Pro")
    for c_id in earbud_buyers_18_25:
        # Purchase PROD-001
        p_date = start_date + timedelta(days=random.randint(10, 100))
        order_count += 1
        item_id = f"ORD-{order_count:06d}"
        prod_x = products[0] # PROD-001
        rev = prod_x["base_price"]
        order_items.append((item_id, c_id, prod_x["product_id"], p_date.strftime("%Y-%m-%d"), 1, 0.0, rev))
        csv_rows.append({
            "order_item_id": item_id, "customer_id": c_id, "age": 22, "segment": "Young Adults (18-25)",
            "product_id": prod_x["product_id"], "product_name": prod_x["name"], "category": prod_x["category"],
            "purchase_date": p_date.strftime("%Y-%m-%d"), "quantity": 1, "discount_pct": 0.0, "revenue": rev
        })

        # Cart event for PROD-002 ("Earbud Case & Charging Stand") with 71% cart abandonment!
        session_count += 1
        s_id = f"SESS-{session_count:06d}"
        s_time = p_date + timedelta(days=random.randint(1, 40))
        sessions.append((s_id, c_id, s_time.strftime("%Y-%m-%d %H:%M:%S"), "Instagram Ads"))

        # Add to cart event
        cart_events.append((f"CART-{len(cart_events)+1:06d}", s_id, c_id, "PROD-002", "add_to_cart", s_time.strftime("%Y-%m-%d %H:%M:%S")))
        
        # 71% abandon, 6% convert, 23% browse without abandon flag
        rand_val = random.random()
        if rand_val < 0.06:
            # Converted!
            cart_events.append((f"CART-{len(cart_events)+1:06d}", s_id, c_id, "PROD-002", "checkout", (s_time + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")))
            order_count += 1
            order_items.append((f"ORD-{order_count:06d}", c_id, "PROD-002", s_time.strftime("%Y-%m-%d"), 1, 0.0, 1200.0))
        elif rand_val < 0.77:
            # Abandoned cart (71% of this segment)
            cart_events.append((f"CART-{len(cart_events)+1:06d}", s_id, c_id, "PROD-002", "abandon", (s_time + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")))

    # Generate general order volume across all customers (~65,000 orders)
    all_customer_ids = [c[0] for c in customers]

    while len(order_items) < 65000:
        c_id = random.choice(all_customer_ids)
        prod = random.choice(products)
        p_date = start_date + timedelta(days=random.randint(1, 175))
        order_count += 1
        disc = random.choice([0.0, 0.0, 0.0, 0.05, 0.10])
        rev = round(prod["base_price"] * (1 - disc), 2)
        item_id = f"ORD-{order_count:06d}"
        order_items.append((item_id, c_id, prod["product_id"], p_date.strftime("%Y-%m-%d"), 1, disc, rev))

    # Generate additional sessions & cart events (~90,000 sessions)
    while len(sessions) < 90000:
        session_count += 1
        s_id = f"SESS-{session_count:06d}"
        c_id = random.choice(all_customer_ids)
        s_time = start_date + timedelta(days=random.randint(1, 175), minutes=random.randint(0, 1440))
        chan = random.choice(channels)
        sessions.append((s_id, c_id, s_time.strftime("%Y-%m-%d %H:%M:%S"), chan))
        
        # Add random cart events
        prod = random.choice(products)
        cart_events.append((f"CART-{len(cart_events)+1:06d}", s_id, c_id, prod["product_id"], "add_to_cart", s_time.strftime("%Y-%m-%d %H:%M:%S")))
        if random.random() < 0.45: # 45% baseline cart abandonment
            cart_events.append((f"CART-{len(cart_events)+1:06d}", s_id, c_id, prod["product_id"], "abandon", (s_time + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")))
        else:
            cart_events.append((f"CART-{len(cart_events)+1:06d}", s_id, c_id, prod["product_id"], "checkout", (s_time + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")))

    print(f"Inserting {len(order_items)} orders, {len(sessions)} sessions, and {len(cart_events)} cart events...")
    cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?, ?)", order_items)
    cursor.executemany("INSERT INTO sessions VALUES (?, ?, ?, ?)", sessions)
    cursor.executemany("INSERT INTO cart_events VALUES (?, ?, ?, ?, ?, ?)", cart_events)

    conn.commit()
    conn.close()

    # Save CSV export
    os.makedirs(DATA_DIR, exist_ok=True)
    df_export = pd.DataFrame(order_items, columns=["order_item_id", "customer_id", "product_id", "purchase_date", "quantity", "discount_pct", "revenue"])
    df_export.to_csv(CSV_PATH, index=False)
    print(f"Synthetic dataset saved to {CSV_PATH} and database seeded successfully.")


if __name__ == "__main__":
    seed_database(force=True)
