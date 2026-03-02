import streamlit as st
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict
from datetime import datetime
import time
import os

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG (MUST be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CSAO Recommendation Engine",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
NODE_COLORS = {
    "Node1_Extension":    "#F5A623",
    "Node2_Texture":      "#A78BFA",
    "Node3_CoOccurrence": "#38BDF8",
    "Node4_Beverage":     "#34D399",
    "Node5_Dessert":      "#F472B6",
    "Node6_BudgetHabit":  "#FB923C",
    "Noise":              "#6B7280",
}
NODE_EXPLANATIONS = {
    "Node1_Extension":    "Physically completes the dish — items that belong together",
    "Node2_Texture":      "Adds sensory contrast — crispy with soft, cooling with spicy",
    "Node3_CoOccurrence": "Collaborative filter — other users who ordered this also added",
    "Node4_Beverage":     "Context-aware drink — matched to cuisine, city, and meal time",
    "Node5_Dessert":      "Regional dessert — weighted by user's personal dessert history",
    "Node6_BudgetHabit":  "Budget optimizer — fits within AOV headroom, habit-aligned",
}

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Clean up Streamlit chrome, but keep header visible for sidebar toggle */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { background: transparent !important; }
.stDeployButton { display: none !important; }

/* ═══════════════════════════════════════════
   ANIMATIONS
   ═══════════════════════════════════════════ */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.03); }
}

/* ═══════════════════════════════════════════
   LAYOUT & BASE
   ═══════════════════════════════════════════ */
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem; max-width: 1400px !important; }

.stApp { 
    background: linear-gradient(135deg, #D4E5E8 0%, #E8F0F2 30%, #D4E5E8 70%, #C8DDE0 100%);
    background-attachment: fixed;
    min-height: 100vh;
}

/* Main text */
.stMarkdown, p, span, label, h1, h2, h3, h4, strong, div { color: #2D2D2D; }

/* ═══════════════════════════════════════════
   SIDEBAR (White Glass Panel)
   ═══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.04) !important;
    animation: slideInLeft 0.5s ease-out;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] strong,
[data-testid="stSidebar"] div { color: #2D2D2D !important; }

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 12px !important;
    color: #2D2D2D !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}
.stSelectbox > div > div:hover { border-color: #F5B800 !important; box-shadow: 0 4px 12px rgba(245,184,0,0.1) !important; }

/* Header */
.sidebar-header { display: flex; align-items: center; gap: 12px; animation: fadeIn 0.6s ease-out; }
.header-icon { width: 44px; height: 44px; border-radius: 14px; background: linear-gradient(135deg, #F5B800, #E5A800); display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 4px 12px rgba(245,184,0,0.3); transition: transform 0.3s ease; }
.header-icon:hover { transform: scale(1.08) rotate(3deg); }
.header-title { font-size: 17px; font-weight: 700; letter-spacing: -0.3px; margin: 0; color: #1A1A1A !important; }
.header-sub { font-size: 11px; color: #8A8A8A !important; margin: 0; }

/* Section Title */
.section-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; color: #999 !important; margin-bottom: 12px; }
.input-label { font-size: 12px; color: #888 !important; margin-bottom: 6px; display: block; }

/* Segment cards */
.seg-card { background: #F3F6F7; border: 2px solid transparent; border-radius: 14px; padding: 12px 8px; text-align: center; transition: all 0.3s ease; cursor: pointer; }
.seg-card:hover { background: #EDF2F4; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.seg-card.active { background: rgba(245,184,0,0.08); border-color: #F5B800; box-shadow: 0 4px 16px rgba(245,184,0,0.15); transform: translateY(-2px); }
.seg-card .name { font-size: 12px; font-weight: 600; color: #2D2D2D !important; }
.seg-card.active .name { color: #D4A000 !important; }
.seg-card .val { font-size: 10px; color: #999 !important; margin-top: 2px; }

/* Diet pill */
.diet-pill-card { padding: 10px 12px; border-radius: 10px; text-align: center; font-size: 12px; font-weight: 600; background: #F3F6F7; border: 2px solid transparent; color: #888 !important; transition: all 0.3s ease; cursor: pointer; }
.diet-pill-card:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.diet-pill-card.veg { background: rgba(34,197,94,0.08); border-color: #22C55E; color: #16a34a !important; }
.diet-pill-card.nv { background: rgba(239,68,68,0.08); border-color: #EF4444; color: #dc2626 !important; }

/* Menu items */
.menu-item-name { font-size: 13px; font-weight: 500; color: #2D2D2D !important; }
.menu-item-meta { font-size: 11px; color: #999 !important; }
.menu-item-price { font-size: 13px; font-weight: 700; color: #D49800 !important; }

/* Cart summary */
.cart-summary { background: #F8FAFB; border: 1px solid rgba(0,0,0,0.06); border-radius: 16px; padding: 20px; margin-top: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); animation: fadeInUp 0.4s ease-out; }
.cart-summary-title { font-size: 14px; font-weight: 700; color: #1A1A1A !important; margin-bottom: 8px; }
.cart-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; font-size: 13px; color: #555 !important; border-bottom: 1px solid rgba(0,0,0,0.04); }
.cart-total-row { display: flex; justify-content: space-between; padding-top: 10px; font-size: 14px; font-weight: 700; color: #D49800 !important; }
.headroom-green { color: #16a34a !important; }
.headroom-amber { color: #D49800 !important; }
.headroom-red { color: #dc2626 !important; }
.section-divider { border: none; border-top: 1px solid rgba(0,0,0,0.06); margin: 16px 0; }

/* ═══════════════════════════════════════════
   MAIN PANEL — KPI Cards
   ═══════════════════════════════════════════ */
.kpi-card { 
    background: rgba(255, 255, 255, 0.9); 
    backdrop-filter: blur(10px); 
    border: 1px solid rgba(0,0,0,0.06); 
    border-radius: 20px; 
    padding: 24px 16px; 
    text-align: center; 
    box-shadow: 0 4px 20px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.02); 
    transition: all 0.35s ease;
    animation: fadeInUp 0.5s ease-out both;
}
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.08); }
.kpi-icon { font-size: 28px; margin-bottom: 10px; }
.kpi-value { font-size: 28px; font-weight: 800; color: #1A1A1A !important; letter-spacing: -0.5px; }
.kpi-label { font-size: 11px; color: #999 !important; font-weight: 600; letter-spacing: 0.5px; margin-top: 4px; text-transform: uppercase; }

/* ═══════════════════════════════════════════
   RECOMMENDATION CARDS (Using Container Hook)
   ═══════════════════════════════════════════ */
div[data-testid="stVerticalBlock"]:has(> div.element-container > div.stMarkdown > div > div.rec-card-hook) {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0,0,0,0.06); 
    border-radius: 20px; 
    padding: 24px 20px 20px 20px; 
    transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94); 
    box-shadow: 0 4px 20px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.02);
    animation: fadeInUp 0.6s ease-out both;
    display: flex;
    flex-direction: column;
    height: 100%;
}
div[data-testid="stVerticalBlock"]:has(> div.element-container > div.stMarkdown > div > div.rec-card-hook):hover {
    transform: translateY(-6px) scale(1.02); 
    box-shadow: 0 16px 40px rgba(0,0,0,0.1); 
    border-color: rgba(245,184,0,0.3); 
}
.rec-node-badge { font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block; }
.rec-item-name { margin-top: 14px; font-size: 16px; font-weight: 700; color: #1A1A1A !important; line-height: 1.3; }
.rec-price { font-size: 20px; font-weight: 800; color: #1A1A1A !important; margin: 4px 0 16px 0; }
.conf-label { font-size: 11px; color: #999 !important; margin-bottom: 6px; margin-top: 12px; }
.conf-bar-bg { background: rgba(0,0,0,0.05); border-radius: 6px; height: 5px; overflow: hidden; margin-bottom: 16px; }
.conf-bar-fill { height: 5px; border-radius: 6px; transition: width 0.8s ease-out; }

/* In-Card Add Button */
div[data-testid="stVerticalBlock"]:has(> div.element-container > div.stMarkdown > div > div.rec-card-hook) .stButton > button {
    border-radius: 14px !important;
    padding: 10px !important;
    width: 100% !important;
    margin-top: auto !important; /* Push to bottom */
}

/* ═══════════════════════════════════════════
   DROPDOWN PORTAL (Dark Pop-up from Ref Image 1)
   ═══════════════════════════════════════════ */
div[role="listbox"] {
    background: #1A1A1D !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
    padding: 4px !important;
}
div[role="listbox"] ul li { color: #888 !important; border-radius: 8px !important; margin-bottom: 2px !important; font-size: 14px !important; }
div[role="listbox"] ul li:hover { color: #FFF !important; background: rgba(255,255,255,0.06) !important; }
div[role="listbox"] ul li[aria-selected="true"] { color: #F5B800 !important; background: rgba(245,184,0,0.1) !important; font-weight: 600 !important; }

/* Log container (keep dark for contrast) */
.log-container { background: #1A1A1A; border-radius: 16px; padding: 1.5rem; font-family: 'Consolas', 'SF Mono', monospace; font-size: 0.82rem; color: #c9d1d9; line-height: 1.7; max-height: 500px; overflow-y: auto; border: 1px solid rgba(255,255,255,0.05); }
.log-header { color: #5BA8B0; font-weight: 700; }
.log-success { color: #F5B800; }
.log-warn { color: #d29922; }
.log-metric { color: #5BA8B0; }
.log-dim { color: #8A8A8A; }

/* ═══════════════════════════════════════════
   BUTTONS (Orange pill style)
   ═══════════════════════════════════════════ */
.stButton > button { 
    background: linear-gradient(135deg, #F5B800, #E5A800) !important; 
    color: #FFFFFF !important; 
    font-weight: 700 !important; 
    border: none !important; 
    border-radius: 14px !important; 
    padding: 10px 20px !important; 
    box-shadow: 0 4px 16px rgba(245,184,0,0.3) !important; 
    transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover { 
    transform: translateY(-2px) scale(1.02) !important; 
    box-shadow: 0 8px 24px rgba(245,184,0,0.4) !important; 
}
.stButton > button:active { 
    transform: translateY(0px) scale(0.98) !important; 
    box-shadow: 0 2px 8px rgba(245,184,0,0.3) !important; 
}
.stButton > button:disabled { 
    background: rgba(0,0,0,0.06) !important; 
    color: #AAAAAA !important; 
    box-shadow: none !important; 
    transform: none !important; 
}

/* Expander */
.streamlit-expanderHeader { 
    background: rgba(255,255,255,0.8) !important; 
    border-radius: 14px !important; 
    color: #2D2D2D !important; 
    border: 1px solid rgba(0,0,0,0.06) !important; 
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
}
.streamlit-expanderHeader:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important; }

/* Empty state */
.empty-state { text-align: center; padding: 80px 20px; animation: fadeIn 0.6s ease-out; }
.empty-state .icon { font-size: 56px; margin-bottom: 16px; }
.empty-state .title { font-size: 20px; font-weight: 700; color: #2D2D2D !important; margin-bottom: 6px; }
.empty-state .sub { font-size: 14px; color: #999 !important; }

/* Footer */
.app-footer { 
    background: rgba(255,255,255,0.8); 
    backdrop-filter: blur(10px); 
    border-top: 1px solid rgba(0,0,0,0.06); 
    padding: 14px 24px; 
    display: flex; 
    justify-content: space-between; 
    font-size: 11px; 
    color: #999 !important; 
    margin-top: 32px; 
    border-radius: 16px 16px 0 0; 
    box-shadow: 0 -2px 12px rgba(0,0,0,0.03);
}

/* Stagger animations for cards in a row. Targeting both the direct KPI card and the Container hook child */
[data-testid="stHorizontalBlock"] > div:nth-child(1) .kpi-card,
[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stVerticalBlock"]:has(> div > div > div > div.rec-card-hook) { animation-delay: 0s; }
[data-testid="stHorizontalBlock"] > div:nth-child(2) .kpi-card,
[data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stVerticalBlock"]:has(> div > div > div > div.rec-card-hook) { animation-delay: 0.08s; }
[data-testid="stHorizontalBlock"] > div:nth-child(3) .kpi-card,
[data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stVerticalBlock"]:has(> div > div > div > div.rec-card-hook) { animation-delay: 0.16s; }
[data-testid="stHorizontalBlock"] > div:nth-child(4) .kpi-card,
[data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stVerticalBlock"]:has(> div > div > div > div.rec-card-hook) { animation-delay: 0.24s; }
[data-testid="stHorizontalBlock"] > div:nth-child(5) [data-testid="stVerticalBlock"]:has(> div > div > div > div.rec-card-hook) { animation-delay: 0.32s; }
</style>

""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA & MODEL (cached)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    users = pd.read_csv("users.csv")
    rests = pd.read_csv("restaurants.csv")
    menu  = pd.read_csv("menu_items.csv")
    orders = pd.read_csv("order_history.csv")
    return users, rests, menu, orders

@st.cache_resource
def load_model():
    return lgb.Booster(model_file="csao_model.txt")

@st.cache_resource
def load_item2vec():
    try:
        from gensim.models import Word2Vec
        if os.path.exists("item2vec.model"):
            return Word2Vec.load("item2vec.model")
    except Exception:
        pass
    return None

@st.cache_data
def build_cooccurrence(orders, _menu):
    """Build item co-occurrence matrix from order history."""
    cooc = defaultdict(lambda: defaultdict(int))
    for _, row in orders.iterrows():
        items_str = str(row.get("items_ordered", ""))
        items = [x.strip() for x in items_str.split(",") if x.strip()]
        for i in range(len(items)):
            for j in range(i+1, len(items)):
                cooc[items[i]][items[j]] += 1
                cooc[items[j]][items[i]] += 1
    return dict(cooc)

@st.cache_data
def load_encoders():
    csao = pd.read_csv("csao_interactions.csv")
    encoders = {}
    for col in ["user_segment", "meal_time", "hexagon_node", "candidate_category",
                "anchor_cuisine", "candidate_cuisine", "city_tier", "price_range"]:
        if col in csao.columns:
            le = LabelEncoder()
            le.fit(csao[col].astype(str))
            encoders[col] = le
    return encoders

users, rests, menu, orders = load_data()
model = load_model()
cooc = build_cooccurrence(orders, menu)
item2vec_model = load_item2vec()
le_map = load_encoders()
max_awo = menu["avg_weekly_orders"].max()

FEATURES = [
    "hexagon_node_enc","is_hexagon_candidate",
    "user_historical_aov","user_segment_enc","price_sensitivity",
    "dessert_affinity","beverage_affinity","total_orders_lifetime",
    "user_item_affinity","user_cuisine_affinity","affinity_match",
    "cart_value","n_items_in_cart","embedding_variance","is_chaos_cart","anchor_cuisine_enc",
    "candidate_price","price_ratio","aov_headroom","price_match","budget_safe",
    "candidate_category_enc","candidate_is_veg","item_popularity_score",
    "hour_of_day","day_of_week","meal_time_enc","city_tier_enc",
    "avg_rating","is_chain",
    "is_beverage","is_dessert","is_extension",
]

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-DETECT MEAL TIME
# ─────────────────────────────────────────────────────────────────────────────
def auto_detect_meal_time():
    hour = datetime.now().hour
    if 6 <= hour < 11:   return "breakfast"
    elif 11 <= hour < 16: return "lunch"
    elif 16 <= hour < 19: return "evening_snack"
    elif 19 <= hour < 23: return "dinner"
    else:                 return "late_night"

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'engine_log' not in st.session_state:
    st.session_state.engine_log = []
if 'recommendations_generated' not in st.session_state:
    st.session_state.recommendations_generated = False
if 'generation_time_ms' not in st.session_state:
    st.session_state.generation_time_ms = None
if 'profile' not in st.session_state:
    st.session_state.profile = {
        'segment': 'mid',
        'is_veg': False,
        'city': 'Mumbai',
        'meal_time': auto_detect_meal_time(),
    }
if 'selected_restaurant' not in st.session_state:
    st.session_state.selected_restaurant = None
if 'category_filter' not in st.session_state:
    st.session_state.category_filter = "All"

# ─────────────────────────────────────────────────────────────────────────────
# HEXAGON CANDIDATE GENERATOR (preserved from original)
# ─────────────────────────────────────────────────────────────────────────────
def generate_candidates(restaurant_id, cart_item_ids, user_row, meal_time, hour):
    """Generate 8-12 candidates using the 6 Hexagon nodes."""
    rest_menu = menu[menu["restaurant_id"] == restaurant_id].copy()
    rest_menu = rest_menu[~rest_menu["item_id"].isin(cart_item_ids)]

    if user_row["is_veg"]:
        rest_menu = rest_menu[rest_menu["is_veg"] == True]

    if len(rest_menu) == 0:
        return pd.DataFrame(), []

    candidates = []
    log_lines = []

    cart_items_info = menu[menu["item_id"].isin(cart_item_ids)]
    anchor_cuisine = cart_items_info["cuisine"].mode().iloc[0] if len(cart_items_info) > 0 else "North Indian"
    cart_value = cart_items_info["price"].sum()
    n_items = len(cart_item_ids)

    cuisines_in_cart = cart_items_info["cuisine"].nunique() if len(cart_items_info) > 0 else 1
    categories_in_cart = cart_items_info["category"].nunique() if len(cart_items_info) > 0 else 1
    embedding_variance = min(0.5, (categories_in_cart * 0.05) + (cuisines_in_cart * 0.1) + np.random.uniform(0, 0.05))
    is_chaos = 1 if embedding_variance >= 0.5 else 0
    aov = user_row["historical_aov"]
    headroom = max(0, aov - cart_value)

    log_lines.append(f'<span class="log-header">═══════════════════════════════════════════════</span>')
    log_lines.append(f'<span class="log-header">  HEXAGON CANDIDATE GENERATOR — ENGINE LOG</span>')
    log_lines.append(f'<span class="log-header">═══════════════════════════════════════════════</span>')
    log_lines.append(f'<span class="log-dim">  Anchor Cuisine: {anchor_cuisine}</span>')
    log_lines.append(f'<span class="log-dim">  Cart Value: ₹{cart_value:.0f}  |  Items: {n_items}  |  AOV: ₹{aov:.0f}</span>')
    log_lines.append(f'<span class="log-dim">  Headroom: ₹{headroom:.0f}  |  Chaos Cart: {"YES ⚡" if is_chaos else "No"}</span>')
    log_lines.append("")

    def add_candidate(item_row, node_name, sim_score=None):
        candidates.append({
            "item_id": item_row["item_id"],
            "item_name": item_row["item_name"],
            "category": item_row["category"],
            "price": item_row["price"],
            "is_veg": item_row["is_veg"],
            "cuisine": item_row["cuisine"],
            "avg_weekly_orders": item_row["avg_weekly_orders"],
            "hexagon_node": node_name,
            "sim_score": sim_score,
        })

    cart_vecs = []
    if item2vec_model is not None:
        for cid in cart_item_ids:
            if cid in item2vec_model.wv:
                cart_vecs.append(item2vec_model.wv[cid])

    def rank_by_similarity(pool, n=2):
        if len(pool) == 0:
            return pd.DataFrame(columns=list(rest_menu.columns) + ["sim_score"])
        if len(cart_vecs) > 0 and item2vec_model is not None:
            avg_cart_vec = np.mean(cart_vecs, axis=0)
            scores = []
            for _, item in pool.iterrows():
                iid = item["item_id"]
                if iid in item2vec_model.wv:
                    ivec = item2vec_model.wv[iid]
                    sim = np.dot(avg_cart_vec, ivec) / (np.linalg.norm(avg_cart_vec) * np.linalg.norm(ivec) + 1e-9)
                    scores.append(sim)
                else:
                    scores.append(-1)
            pool = pool.copy()
            pool["sim_score"] = scores
            return pool.sort_values("sim_score", ascending=False).head(n)
        pool = pool.copy()
        pool["sim_score"] = 0.0
        return pool.head(n)

    def get_cuisine_pool(category, n=2, prefer_cuisine=True):
        if prefer_cuisine:
            pool = rest_menu[(rest_menu["category"] == category) & (rest_menu["cuisine"] == anchor_cuisine)]
            if len(pool) >= n:
                return rank_by_similarity(pool, n)
            pool = rest_menu[rest_menu["category"] == category]
            return rank_by_similarity(pool, n)
        else:
            pool = rest_menu[rest_menu["category"] == category]
            return rank_by_similarity(pool, n)

    used_ids = set(cart_item_ids)

    # Node 1: Extension
    n1 = get_cuisine_pool("Extension", 2)
    n1 = n1[~n1["item_id"].isin(used_ids)]
    for _, item in n1.iterrows():
        add_candidate(item, "Node1_Extension", item.get("sim_score"))
        used_ids.add(item["item_id"])
    n1_names = [f'{r["item_name"]} (sim: {r.get("sim_score", 0):.2f})' for _, r in n1.iterrows()]
    log_lines.append(f'  <span class="log-success">Node1 Extension:</span>  {len(n1)} candidates (cuisine-matched + Item2Vec)')
    for nm in n1_names:
        log_lines.append(f'    → {nm}')

    # Node 2: Texture (Side)
    n2 = get_cuisine_pool("Side", 2)
    n2 = n2[~n2["item_id"].isin(used_ids)]
    for _, item in n2.iterrows():
        add_candidate(item, "Node2_Texture", item.get("sim_score"))
        used_ids.add(item["item_id"])
    n2_names = [f'{r["item_name"]} (sim: {r.get("sim_score", 0):.2f})' for _, r in n2.iterrows()]
    log_lines.append(f'  <span class="log-success">Node2 Texture:</span>    {len(n2)} candidates (cuisine-matched + Item2Vec)')
    for nm in n2_names:
        log_lines.append(f'    → {nm}')

    # Node 3: Co-occurrence
    cooc_scores = defaultdict(int)
    for cid in cart_item_ids:
        if cid in cooc:
            for co_id, cnt in cooc[cid].items():
                if co_id not in used_ids:
                    cooc_scores[co_id] += cnt
    cooc_rest_items = rest_menu[rest_menu["item_id"].isin(cooc_scores.keys())]
    cooc_same_cuisine = cooc_rest_items[cooc_rest_items["cuisine"] == anchor_cuisine]
    if len(cooc_same_cuisine) >= 2:
        n3 = rank_by_similarity(cooc_same_cuisine, 2)
    else:
        n3 = rank_by_similarity(cooc_rest_items, 2)
    n3 = n3[~n3["item_id"].isin(used_ids)]
    for _, item in n3.iterrows():
        add_candidate(item, "Node3_CoOccurrence", item.get("sim_score"))
        used_ids.add(item["item_id"])
    log_lines.append(f'  <span class="log-success">Node3 CoOccur:</span>   {len(n3)} candidates (co-purchase + cuisine filter)')
    for _, r in n3.iterrows():
        log_lines.append(f'    → {r["item_name"]} (sim: {r.get("sim_score", 0):.2f})')

    # Node 4: Beverage
    bev_pool = rest_menu[(rest_menu["category"] == "Beverage") & (~rest_menu["item_id"].isin(used_ids))]
    n4 = rank_by_similarity(bev_pool, 2)
    for _, item in n4.iterrows():
        add_candidate(item, "Node4_Beverage", item.get("sim_score"))
        used_ids.add(item["item_id"])
    log_lines.append(f'  <span class="log-success">Node4 Beverage:</span>  {len(n4)} candidates (Item2Vec ranked)')
    for _, r in n4.iterrows():
        log_lines.append(f'    → {r["item_name"]} (sim: {r.get("sim_score", 0):.2f})')

    # Node 5: Dessert
    des_pool = rest_menu[(rest_menu["category"] == "Dessert") & (~rest_menu["item_id"].isin(used_ids))]
    n5 = rank_by_similarity(des_pool, 2)
    for _, item in n5.iterrows():
        add_candidate(item, "Node5_Dessert", item.get("sim_score"))
        used_ids.add(item["item_id"])
    log_lines.append(f'  <span class="log-success">Node5 Dessert:</span>   {len(n5)} candidates (Item2Vec ranked)')
    for _, r in n5.iterrows():
        log_lines.append(f'    → {r["item_name"]} (sim: {r.get("sim_score", 0):.2f})')

    # Node 6: Budget/Habit
    budget_pool = rest_menu[(rest_menu["price"] <= max(headroom * 0.5, 50)) &
                            (~rest_menu["category"].isin(["Main", "Beverage", "Dessert"])) &
                            (~rest_menu["item_id"].isin(used_ids))]
    n6 = rank_by_similarity(budget_pool, 2)
    for _, item in n6.iterrows():
        add_candidate(item, "Node6_BudgetHabit", item.get("sim_score"))
        used_ids.add(item["item_id"])
    log_lines.append(f'  <span class="log-success">Node6 Budget:</span>    {len(n6)} candidates (within ₹{max(headroom*0.5, 50):.0f} + Item2Vec)')
    for _, r in n6.iterrows():
        log_lines.append(f'    → {r["item_name"]} (sim: {r.get("sim_score", 0):.2f})')

    log_lines.append("")
    log_lines.append(f'  <span class="log-metric">Total candidates generated: {len(candidates)}</span>')

    # Deduplicate
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c["item_id"] not in seen:
            seen.add(c["item_id"])
            unique_candidates.append(c)
    candidates = unique_candidates

    if len(candidates) == 0:
        return pd.DataFrame(), log_lines

    # Build feature DataFrame
    cdf = pd.DataFrame(candidates)
    cdf["cart_value"] = cart_value
    cdf["n_items_in_cart"] = n_items
    cdf["embedding_variance"] = embedding_variance
    cdf["is_chaos_cart"] = is_chaos
    cdf["anchor_cuisine"] = anchor_cuisine
    cdf["user_historical_aov"] = aov
    cdf["aov_headroom"] = headroom
    cdf["price_ratio"] = cdf["price"] / max(cart_value, 1)
    cdf["candidate_price"] = cdf["price"]
    cdf["candidate_is_veg"] = cdf["is_veg"].astype(int)
    cdf["candidate_category"] = cdf["category"]
    cdf["candidate_cuisine"] = cdf["cuisine"]

    base_pop = cdf["avg_weekly_orders"] / max(max_awo, 1)
    cdf["item_popularity_score"] = np.clip(base_pop + np.random.normal(0, 0.15, len(cdf)), 0, 1)

    cdf["user_segment"] = user_row["user_segment"]
    cdf["meal_time"] = meal_time
    cdf["hour_of_day"] = hour
    cdf["day_of_week"] = 3
    cdf["city_tier"] = user_row["city_tier"]
    cdf["is_hexagon_candidate"] = 1
    cdf["price_sensitivity"] = user_row.get("price_sensitivity", 0.5)
    cdf["dessert_affinity"] = user_row.get("dessert_affinity", 0.5)
    cdf["beverage_affinity"] = user_row.get("beverage_affinity", 0.5)
    cdf["total_orders_lifetime"] = user_row.get("total_orders_lifetime", 20)
    cdf["user_item_affinity"] = 0.049
    cdf["user_cuisine_affinity"] = np.where(cdf["cuisine"] == user_row.get("preferred_cuisine", ""), 0.35, 0.15)
    cdf["affinity_match"] = np.where(cdf["category"]=="Beverage", cdf["beverage_affinity"],
                            np.where(cdf["category"]=="Dessert", cdf["dessert_affinity"], 0.5))
    cdf["price_match"] = (cdf["candidate_is_veg"] == int(user_row["is_veg"])).astype(int)
    cdf["budget_safe"] = (cdf["candidate_price"] <= headroom * 0.4).astype(int)
    cdf["is_beverage"] = (cdf["category"] == "Beverage").astype(int)
    cdf["is_dessert"] = (cdf["category"] == "Dessert").astype(int)
    cdf["is_extension"] = (cdf["category"] == "Extension").astype(int)

    rest_info = rests[rests["restaurant_id"] == restaurant_id].iloc[0]
    cdf["avg_rating"] = rest_info["avg_rating"]
    cdf["is_chain"] = int(rest_info["is_chain"])
    cdf["price_range"] = rest_info["price_range"]

    for col in ["user_segment", "meal_time", "hexagon_node", "candidate_category",
                "anchor_cuisine", "candidate_cuisine", "city_tier", "price_range"]:
        if col in le_map and col in cdf.columns:
            try:
                cdf[col + "_enc"] = le_map[col].transform(cdf[col].astype(str))
            except ValueError:
                cdf[col + "_enc"] = 0

    return cdf, log_lines


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def run_recommendation_pipeline():
    """Run the full pipeline and store results in session state."""
    cart = st.session_state.cart
    if len(cart) == 0:
        st.session_state.recommendations = None
        st.session_state.recommendations_generated = False
        return

    cart_item_ids = list(cart.keys())
    profile = st.session_state.profile
    rid = st.session_state.selected_restaurant

    if rid is None:
        return

    # Build user row
    matching_users = users[(users["city"] == profile['city']) &
                           (users["user_segment"] == profile['segment']) &
                           (users["is_veg"] == profile['is_veg'])]
    if len(matching_users) > 0:
        user_row = matching_users.iloc[0]
    else:
        user_row = users[users["city"] == profile['city']].iloc[0] if len(users[users["city"] == profile['city']]) > 0 else users.iloc[0]

    meal_time = profile['meal_time']
    hour_map = {"breakfast": 9, "lunch": 13, "evening_snack": 17, "dinner": 20, "late_night": 23}
    hour = hour_map.get(meal_time, 20)

    t0 = time.time()
    cdf, log_lines = generate_candidates(rid, cart_item_ids, user_row, meal_time, hour)
    t_gen = time.time() - t0

    if len(cdf) > 0:
        available_features = [f for f in FEATURES if f in cdf.columns]
        X_demo = cdf[available_features].fillna(0)
        for f in FEATURES:
            if f not in X_demo.columns:
                X_demo[f] = 0
        X_demo = X_demo[FEATURES]

        t1 = time.time()
        cdf["score"] = model.predict(X_demo)
        t_pred = time.time() - t1
        t_total = (t_gen + t_pred) * 1000

        cdf = cdf.sort_values("score", ascending=False).reset_index(drop=True)

        # Add scoring section to log
        log_lines.append("")
        log_lines.append(f'<span class="log-header">═══════════════════════════════════════════════</span>')
        log_lines.append(f'<span class="log-header">  LIGHTGBM RANKER — SCORING</span>')
        log_lines.append(f'<span class="log-header">═══════════════════════════════════════════════</span>')
        log_lines.append(f'  <span class="log-dim">Features used: {len(FEATURES)}</span>')
        log_lines.append(f'  <span class="log-dim">Candidates scored: {len(cdf)}</span>')
        if len(cdf) > 0:
            log_lines.append(f'  <span class="log-dim">Top score: {cdf.iloc[0]["score"]:.4f} ({cdf.iloc[0]["item_name"]} — {cdf.iloc[0]["hexagon_node"]})</span>')
        log_lines.append(f'  <span class="log-success">Inference time: {t_pred*1000:.1f}ms</span>')
        log_lines.append("")
        log_lines.append(f'<span class="log-header">═══════════════════════════════════════════════</span>')
        log_lines.append(f'<span class="log-header">  PERFORMANCE</span>')
        log_lines.append(f'<span class="log-header">═══════════════════════════════════════════════</span>')
        log_lines.append(f'  <span class="log-success">Candidate generation: {t_gen*1000:.1f}ms</span>')
        log_lines.append(f'  <span class="log-success">LightGBM inference:   {t_pred*1000:.1f}ms</span>')
        log_lines.append(f'  <span class="log-metric">Total latency:        {t_total:.1f}ms  {"✅ PASS (<300ms)" if t_total < 300 else "⚠️ SLOW"}</span>')

        st.session_state.recommendations = cdf
        st.session_state.engine_log = log_lines
        st.session_state.generation_time_ms = t_total
        st.session_state.recommendations_generated = True
    else:
        st.session_state.recommendations = None
        st.session_state.engine_log = log_lines


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# TWO-PANEL DASHBOARD LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Left Panel (Profile + Cart)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Header ──
    st.markdown("""
    <div class="sidebar-header">
        <div class="header-icon">🛍️</div>
        <div>
            <p class="header-title">CSAO Recommendations</p>
            <p class="header-sub">Cart Add-On System</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── USER PROFILE ──
    st.markdown('<span class="section-title">User Profile</span>', unsafe_allow_html=True)
    st.markdown('<span class="input-label">User Segment</span>', unsafe_allow_html=True)

    seg_cols = st.columns(3)
    segments = [("Budget", "~₹200"), ("Mid", "~₹450"), ("Premium", "~₹750")]
    for i, (label, val) in enumerate(segments):
        with seg_cols[i]:
            active = "active" if st.session_state.profile['segment'] == label.lower() else ""
            st.markdown(f"""<div class="seg-card {active}">
                <div class="name">{label}</div><div class="val">{val}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(label, key=f"seg_{label}", use_container_width=True):
                st.session_state.profile['segment'] = label.lower()
                if st.session_state.recommendations_generated:
                    run_recommendation_pipeline()
                st.rerun()

    st.markdown('<span class="input-label">Dietary Preference</span>', unsafe_allow_html=True)
    diet_cols = st.columns(2)
    with diet_cols[0]:
        veg_cls = "veg" if st.session_state.profile['is_veg'] else ""
        st.markdown(f'<div class="diet-pill-card {veg_cls}">Vegetarian</div>', unsafe_allow_html=True)
        if st.button("Veg", key="diet_veg", use_container_width=True):
            st.session_state.profile['is_veg'] = True
            st.session_state.cart = {}
            st.session_state.recommendations = None
            st.session_state.recommendations_generated = False
            st.rerun()
    with diet_cols[1]:
        nv_cls = "nv" if not st.session_state.profile['is_veg'] else ""
        st.markdown(f'<div class="diet-pill-card {nv_cls}">Non-Veg</div>', unsafe_allow_html=True)
        if st.button("Non-Veg", key="diet_nv", use_container_width=True):
            st.session_state.profile['is_veg'] = False
            st.session_state.cart = {}
            st.session_state.recommendations = None
            st.session_state.recommendations_generated = False
            st.rerun()

    # Meal Time Dropdown
    st.markdown('<span class="input-label">Meal Time</span>', unsafe_allow_html=True)
    times = ["Lunch (12:00 PM - 3:00 PM)", "Dinner (7:00 PM - 11:00 PM)", "Snacks (4:00 PM - 6:00 PM)", "Breakfast (8:00 AM - 11:00 AM)"]
    time_keys = ["lunch", "dinner", "evening_snack", "breakfast"]
    cur_meal = st.session_state.profile.get('meal_time', 'lunch')
    def_idx = time_keys.index(cur_meal) if cur_meal in time_keys else 0
    sel_time = st.selectbox("Meal Time", times, index=def_idx, key="meal_select", label_visibility="collapsed")
    new_key = time_keys[times.index(sel_time)]
    if new_key != cur_meal:
        st.session_state.profile['meal_time'] = new_key
        if st.session_state.recommendations_generated:
            run_recommendation_pipeline()
        st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── CURRENT CART ──
    st.markdown('<span class="section-title">Current Cart</span>', unsafe_allow_html=True)

    # Restaurant Selector
    st.markdown('<span class="input-label">Restaurant</span>', unsafe_allow_html=True)
    city_rests = rests[rests["city"] == st.session_state.profile['city']].copy()
    rest_options = city_rests[["restaurant_id", "name", "cuisine_primary"]].copy()
    rest_options["display"] = rest_options["name"] + " (" + rest_options["cuisine_primary"] + ")"
    rest_display_list = rest_options["display"].tolist()

    rest_choice = st.selectbox("Restaurant", rest_display_list, key="rest_select", label_visibility="collapsed")
    if rest_choice:
        selected_rest = rest_options[rest_options["display"] == rest_choice].iloc[0]
        rid = selected_rest["restaurant_id"]
        if st.session_state.selected_restaurant != rid:
            st.session_state.selected_restaurant = rid
            st.session_state.cart = {}
            st.session_state.recommendations = None
            st.session_state.recommendations_generated = False

        # Menu items
        rest_menu_full = menu[menu["restaurant_id"] == rid].copy()
        if st.session_state.profile['is_veg']:
            rest_menu_display = rest_menu_full[rest_menu_full["is_veg"] == True]
        else:
            rest_menu_display = rest_menu_full

        mains = rest_menu_display[rest_menu_display["category"] == "Main"].head(5)
        others = rest_menu_display[rest_menu_display["category"] != "Main"].head(5)
        filtered_menu = pd.concat([mains, others])

        for _, item in filtered_menu.iterrows():
            item_id = item["item_id"]
            if item_id in st.session_state.cart:
                continue
            veg_dot = "🟢" if item["is_veg"] else "🔴"
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(f"**{veg_dot} {item['item_name']}**")
                st.caption(f"₹{item['price']:.0f}")
            with c3:
                if st.button("➕", key=f"add_{item_id}"):
                    st.session_state.cart[item_id] = item.to_dict()
                    st.toast(f"✓ {item['item_name']} added", icon="🛒")
                    if st.session_state.recommendations_generated:
                        run_recommendation_pipeline()
                    st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Cart Summary (pinned at bottom) ──
    if len(st.session_state.cart) > 0:
        cart_items_df = pd.DataFrame(st.session_state.cart.values())
        cart_total = cart_items_df["price"].sum()

        profile = st.session_state.profile
        matching = users[(users["city"] == profile['city']) & (users["user_segment"] == profile['segment']) & (users["is_veg"] == profile['is_veg'])]
        user_aov = matching.iloc[0]["historical_aov"] if len(matching) > 0 else 400
        headroom = max(0, user_aov - cart_total)

        if headroom > 200: hr_class = "headroom-green"
        elif headroom > 50: hr_class = "headroom-amber"
        else: hr_class = "headroom-red"

        cart_html = f'<div class="cart-summary"><div class="cart-summary-title">🛒 YOUR CART ({len(st.session_state.cart)} items)</div>'
        for iid, idata in st.session_state.cart.items():
            dot_color = "#22c55e" if idata.get("is_veg", True) else "#ef4444"
            vdot = f'<span style="display:inline-block; width:10px; height:10px; background-color:{dot_color}; border-radius:50%; margin-right:8px; vertical-align:middle;"></span>'
            cart_html += f'<div class="cart-row"><span style="display:flex; align-items:center;">{vdot}{idata["item_name"]}</span><span>₹{idata["price"]:.0f}</span></div>'
        cart_html += f'<div class="cart-total-row"><span>Subtotal</span><span>₹{cart_total:.0f}</span></div>'
        cart_html += f'<div class="cart-row"><span>Items</span><span>{len(st.session_state.cart)}</span></div>'
        cart_html += f'<div class="cart-row"><span class="{hr_class}">Available Budget</span><span class="{hr_class}">₹{headroom:.0f}</span></div>'
        cart_html += '</div>'
        st.markdown(cart_html, unsafe_allow_html=True)

        for iid in list(st.session_state.cart.keys()):
            iname = st.session_state.cart[iid]["item_name"]
            if st.button(f"✕ {iname[:20]}", key=f"rm_{iid}"):
                del st.session_state.cart[iid]
                if st.session_state.recommendations_generated:
                    if len(st.session_state.cart) > 0: run_recommendation_pipeline()
                    else:
                        st.session_state.recommendations = None
                        st.session_state.recommendations_generated = False
                st.rerun()

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        if st.button("↻ Update Recommendations", key="gen_btn", use_container_width=True):
            run_recommendation_pipeline()
            st.rerun()
    else:
        st.markdown("""
        <div class="cart-summary" style="text-align:center; padding: 20px;">
            <div style="font-size: 32px; margin-bottom: 8px;">🛒</div>
            <div style="color: #8A8A8A; font-size: 13px;">Your cart is empty</div>
            <div style="color: #666; font-size: 12px;">Add items from the menu above</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN AREA — Right Panel (KPIs + Recommendations + Insights)
# ─────────────────────────────────────────────────────────────────────────────

# ── KPI Row ──
if len(st.session_state.cart) > 0:
    cart_items_df = pd.DataFrame(st.session_state.cart.values())
    cart_total = cart_items_df["price"].sum()
    profile = st.session_state.profile
    matching = users[(users["city"] == profile['city']) & (users["user_segment"] == profile['segment']) & (users["is_veg"] == profile['is_veg'])]
    user_aov = matching.iloc[0]["historical_aov"] if len(matching) > 0 else 400
    headroom = max(0, user_aov - cart_total)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-icon">🛒</div><div class="kpi-value">₹{cart_total:.0f}</div><div class="kpi-label">CART VALUE</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-icon">📊</div><div class="kpi-value">₹{user_aov:.0f}</div><div class="kpi-label">USER AOV</div></div>', unsafe_allow_html=True)
    with k3:
        hr_color = "#22C55E" if headroom > 200 else "#F5B800" if headroom > 50 else "#EF4444"
        st.markdown(f'<div class="kpi-card"><div class="kpi-icon">💰</div><div class="kpi-value" style="color:{hr_color}">₹{headroom:.0f}</div><div class="kpi-label">HEADROOM</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-icon">📦</div><div class="kpi-value">{len(st.session_state.cart)}</div><div class="kpi-label">ITEMS</div></div>', unsafe_allow_html=True)

    st.markdown("")

# ── Recommendation Rail (5-column grid) ──
if st.session_state.recommendations is not None and len(st.session_state.recommendations) > 0:
    cdf = st.session_state.recommendations
    top_recs = cdf.nlargest(5, 'score').reset_index(drop=True)

    gen_time = st.session_state.generation_time_ms
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px;">
        <div>
            <div style="font-size:20px; font-weight:700; color:#1A1A1A; letter-spacing:-0.3px;">Recommended Add-Ons</div>
            <div style="font-size:13px; color:#888;">Based on order patterns and user preferences</div>
        </div>
        <div style="font-size:12px; color:#888; display:flex; gap:12px; align-items:center;">
            <span>✅ Model: LightGBM v2.4</span>
            <span>•</span>
            <span>Latency: {gen_time:.0f}ms</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    for i, (_, rec) in enumerate(top_recs.iterrows()):
        with cols[i]:
            node = rec['hexagon_node']
            color = NODE_COLORS.get(node, '#888888')
            node_label = node.split('_', 1)[1] if '_' in node else node
            confidence = int(rec['score'] * 100)

            with st.container():
                st.markdown(f"""
                <div class="rec-card-hook"></div>
                <span class="rec-node-badge" style="background:{color}15; color:{color};">{node_label}</span>
                <span style="float:right; font-size:11px; font-weight:700; color:#BBB;">#{i+1}</span>
                <div class="rec-item-name">{rec['item_name']}</div>
                <div class="rec-price">₹{rec['price']:.0f}</div>
                <div class="conf-label">Confidence: {confidence}%</div>
                <div class="conf-bar-bg">
                    <div class="conf-bar-fill" style="background:{color}; width:{confidence}%;"></div>
                </div>
                """, unsafe_allow_html=True)

                rec_item_id = rec['item_id']
                if rec_item_id not in st.session_state.cart:
                    if st.button("Add to Cart", key=f"rec_add_{rec_item_id}", use_container_width=True):
                        item_data = menu[menu["item_id"] == rec_item_id].iloc[0].to_dict()
                        st.session_state.cart[rec_item_id] = item_data
                        st.toast(f"✓ {rec['item_name']} added!", icon="✨")
                        run_recommendation_pipeline()
                        st.rerun()
                else:
                    st.markdown('<div style="text-align:center; color:#16a34a; font-size:12px; font-weight:700; padding:10px;">✓ In Cart</div>', unsafe_allow_html=True)

    st.markdown("")

    # ── Recommendation Insights ──
    with st.expander("📈 Recommendation Insights"):
        for node_name in top_recs['hexagon_node'].unique():
            color = NODE_COLORS.get(node_name, '#888')
            node_items = top_recs[top_recs['hexagon_node'] == node_name]
            explanation = NODE_EXPLANATIONS.get(node_name, "")
            items_list = ', '.join(node_items['item_name'].tolist())
            st.markdown(f"""
            <div style="border-left: 3px solid {color}; padding-left: 12px; margin: 8px 0;">
                <strong style="color: {color};">{node_name}</strong><br>
                <span style="color: #888; font-size: 13px;">{explanation}</span><br>
                <span style="color: #2D2D2D; font-size: 13px;">Recommended: {items_list}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Engine Log ──
    with st.expander("🔧 Engine Log (Transparency Console)", expanded=False):
        log_html = '<div class="log-container">'
        for line in st.session_state.engine_log:
            log_html += line + "<br>"
        log_html += "</div>"
        st.markdown(log_html, unsafe_allow_html=True)

elif len(st.session_state.cart) > 0 and not st.session_state.recommendations_generated:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">⚡</div>
        <div class="title">Ready to generate</div>
        <div class="sub">Click "Update Recommendations" in the sidebar</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🛒</div>
        <div class="title">Your cart is empty</div>
        <div class="sub">Add items from the menu to see CSAO recommendations</div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ──
st.markdown("""
<div class="app-footer">
    <div>CSAO Recommendation System v2.4 • Hexagon + LightGBM Architecture • AUC: 0.7741 (+31.4% vs baseline)</div>
    <div style="color: #16a34a; display: flex; align-items: center; gap: 8px;">
        <div style="width: 8px; height: 8px; background: #16a34a; border-radius: 50%;"></div> System Active
    </div>
</div>
""", unsafe_allow_html=True)
