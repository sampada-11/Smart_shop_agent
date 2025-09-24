import os
import io
import base64
import random
import datetime as dt
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


# -------------------------------
# Page & Theme
# -------------------------------
st.set_page_config(
    page_title="Smart Shopping Pulse",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

custom_css = """
<style>
.app-card {border:1px solid #e6e6e6;border-radius:12px;padding:16px;background:#ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.app-pill {display:inline-block;padding:2px 8px;border-radius:999px;background:#f6f7f9;font-size:12px;margin-right:6px}
.price {font-weight:700;color:#0f766e}
.rating {font-weight:600;color:#f59e0b}
.site {color:#475569}
.section-title {margin-top:0.25rem;margin-bottom:0.5rem}
.stTabs [data-baseweb="tab-list"] {gap: 8px}
.stTabs [data-baseweb="tab"] {background:#f6f7f9;border-radius:10px;padding:10px 14px}
.stTabs [aria-selected="true"] {background:#ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# -------------------------------
# Config & Helpers
# -------------------------------
DEFAULT_LANGFLOW_URL = os.environ.get("LANGFLOW_URL", "http://localhost:7860/api/v1/run/231292dc-aa6c-449a-b565-dbcf5667ff23")
DEFAULT_LANGFLOW_KEY = os.environ.get("LANGFLOW_API_KEY", "")
IBM_WATSON_API_KEY = os.environ.get("IBM_WATSON_API_KEY", "")
IBM_WATSON_URL = os.environ.get("IBM_WATSON_URL", "")
LANGFLOW_COMPONENTS_PATH = os.environ.get("LANGFLOW_COMPONENTS_PATH", "")


def try_langflow(query_text: str, api_url: str, api_key: str) -> Optional[str]:
    if not api_url or not api_key or not query_text:
        return None
    try:
        payload = {"output_type": "chat", "input_type": "chat", "input_value": query_text}
        headers = {"Content-Type": "application/json", "x-api-key": api_key}
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception:
        return None


def stub_multisource_aggregate(
    text_query: Optional[str],
    image: Optional[Image.Image],
    audio_bytes: Optional[bytes]
) -> pd.DataFrame:
    random.seed(42)
    sample = [
        {"product": "Wireless Noise-Canceling Headphones", "site": "ShopA", "price": 199.99, "rating": 4.6, "reviews": 1320, "sustainability": 72, "url": "https://shopa.example/wnc-headphones"},
        {"product": "Wireless Noise-Canceling Headphones", "site": "ShopB", "price": 189.49, "rating": 4.4, "reviews": 860, "sustainability": 70, "url": "https://shopb.example/wnc-headphones"},
        {"product": "Wireless Noise-Canceling Headphones", "site": "ShopC", "price": 209.00, "rating": 4.7, "reviews": 2210, "sustainability": 78, "url": "https://shopc.example/wnc-headphones"},
        {"product": "Over-Ear Studio Headphones", "site": "ShopA", "price": 149.99, "rating": 4.3, "reviews": 540, "sustainability": 65, "url": "https://shopa.example/studio-overear"},
        {"product": "Over-Ear Studio Headphones", "site": "ShopB", "price": 139.50, "rating": 4.2, "reviews": 610, "sustainability": 62, "url": "https://shopb.example/studio-overear"},
        {"product": "On-Ear Lightweight Headphones", "site": "ShopC", "price": 89.00, "rating": 4.0, "reviews": 410, "sustainability": 60, "url": "https://shopc.example/lite-on-ear"}
    ]
    df = pd.DataFrame(sample)
    # Simple heuristic adjustments for multimodal inputs
    if image is not None:
        df["rating"] = (df["rating"] + 0.05).clip(upper=5.0)
    if audio_bytes is not None:
        df["price"] = (df["price"] * 0.98).round(2)
    if text_query:
        df["match_score"] = [0.92, 0.90, 0.94, 0.78, 0.76, 0.68]
    else:
        df["match_score"] = [0.80, 0.78, 0.82, 0.70, 0.69, 0.60]
    return df


def agentic_suggestions(df: pd.DataFrame) -> List[str]:
    tips: List[str] = []
    if df.empty:
        return ["No data available to generate suggestions."]
    min_price = df["price"].min()
    best_row = df.loc[df["price"].idxmin()]
    tips.append(f"Best current price is {min_price:.2f} on {best_row['site']}. Consider buying now if under budget.")

    month = dt.datetime.now().month
    if month in [11, 12]:
        tips.append("Expect holiday discounts. Watch for Black Friday/Cyber Monday drops.")
    if month in [7, 8]:
        tips.append("Back-to-school promotions may reduce prices on audio gear.")

    if (df["reviews"].max() > 2000) and (df["rating"].mean() < 4.3):
        tips.append("Potential review manipulation detected: very high volume with inconsistent ratings. Verify third-party sources.")

    drops = [round(random.uniform(2, 8), 1) for _ in range(2)]
    tips.append(f"Set price-drop alert thresholds at {drops[0]}% and {drops[1]}% for timely notifications.")
    alt = df.sort_values(["price", "sustainability"], ascending=[True, False]).head(1).iloc[0]
    tips.append(f"Alternative recommendation: {alt['product']} on {alt['site']} with sustainability {alt['sustainability']}.")
    return tips


def to_image_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def render_product_card(row: pd.Series):
    st.markdown(
        f"""
        <div class="app-card">
            <div class="section-title"><strong>{row['product']}</strong></div>
            <div class="site">{row['site']}</div>
            <div style="margin:8px 0">
                <span class="price">${row['price']:.2f}</span>
                <span class="app-pill rating">⭐ {row['rating']:.1f}</span>
                <span class="app-pill">{row['reviews']} reviews</span>
                <span class="app-pill">Match {row['match_score']*100:.0f}%</span>
                <span class="app-pill">Sustainability {row['sustainability']}</span>
            </div>
            <a href="{row['url']}" target="_blank">Buy on {row['site']}</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------
# Sidebar Controls
# -------------------------------
with st.sidebar:
    st.header("Controls")
    api_url = st.text_input("Langflow API URL", value=DEFAULT_LANGFLOW_URL)
    api_key = st.text_input("Langflow API Key", value=DEFAULT_LANGFLOW_KEY, type="password")
    st.caption(f"IBM Watson URL: {IBM_WATSON_URL or 'not set'}")
    st.divider()
    price_range = st.slider("Price range", 50, 500, (80, 250))
    min_rating = st.slider("Minimum rating", 1.0, 5.0, 4.0, 0.1)
    sustain_weight = st.slider("Sustainability importance", 0, 100, 50)
    st.caption("Adjust filters to refine comparisons across sources.")


# -------------------------------
# Main Layout
# -------------------------------
st.title("🛍️ Smart Shopping Pulse")
st.caption("Multisource comparisons, multimodal search, predictive suggestions, and a personal shopping pulse dashboard.")

tab_search, tab_dashboard = st.tabs(["Search", "Dashboard"])


with tab_search:
    col1, col2, col3 = st.columns([2, 1.2, 1.2])
    with col1:
        text_query = st.text_area("Describe what you want", placeholder="e.g., noise-canceling wireless headphones under $200 with good battery...")
        if st.button("Search", type="primary"):
            st.session_state["__do_search__"] = True
    with col2:
        image_file = st.file_uploader("Upload a product image", type=["png", "jpg", "jpeg"])
        image_obj = Image.open(image_file).convert("RGB") if image_file else None
        if image_obj is not None:
            st.image(image_obj, caption="Query image", use_column_width=True)
    with col3:
        audio_file = st.file_uploader("Upload voice query (wav/mp3)", type=["wav", "mp3", "m4a"])
        audio_bytes: Optional[bytes] = audio_file.read() if audio_file else None
        if audio_file is not None:
            st.audio(audio_bytes)

    if st.session_state.get("__do_search__"):
        with st.spinner("Aggregating data across sources..."):
            df = stub_multisource_aggregate(text_query, image_obj, audio_bytes)
            df = df[(df["price"] >= price_range[0]) & (df["price"] <= price_range[1])]
            df = df[df["rating"] >= min_rating]
            if sustain_weight > 50:
                df = df.sort_values(["sustainability", "price"], ascending=[False, True])
            else:
                df = df.sort_values(["price", "rating"], ascending=[True, False])

        st.subheader("Top Matches")
        if df.empty:
            st.info("No products match the current filters.")
        else:
            grid_cols = st.columns(3)
            for i, (_, row) in enumerate(df.head(6).iterrows()):
                with grid_cols[i % 3]:
                    render_product_card(row)

        st.subheader("Agentic Suggestions")
        suggestions = agentic_suggestions(df)
        for s in suggestions:
            st.write("- " + s)

        if text_query:
            st.subheader("LLM Insights")
            llm_resp = try_langflow(text_query, api_url, api_key)
            if llm_resp:
                st.success(llm_resp)
            else:
                st.caption("No response from Langflow or not configured.")


with tab_dashboard:
    st.subheader("Shopping Pulse Dashboard")
    if "__history__" not in st.session_state:
        st.session_state["__history__"] = stub_multisource_aggregate("seed", None, None)
    hist = st.session_state["__history__"]

    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("**Price vs. Rating by Site**")
        fig = px.scatter(hist, x="price", y="rating", color="site", size="reviews", hover_name="product")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Sustainability Scores**")
        fig2 = px.box(hist, x="site", y="sustainability", color="site")
        st.plotly_chart(fig2, use_container_width=True)
    with right:
        st.markdown("**Trending Products**")
        trend = hist.groupby("product").agg({"reviews": "sum", "rating": "mean"}).reset_index()
        trend = trend.sort_values("reviews", ascending=False)
        st.dataframe(trend, use_container_width=True, height=260)
        st.markdown("**Personal Shopping List**")
        if "shopping_list" not in st.session_state:
            st.session_state["shopping_list"] = []
        new_item = st.text_input("Add item")
        add = st.button("Add")
        if add and new_item:
            st.session_state["shopping_list"].append(new_item)
        if st.session_state["shopping_list"]:
            st.write("\n".join([f"• {x}" for x in st.session_state["shopping_list"]]))
