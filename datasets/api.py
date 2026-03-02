import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict
from datetime import datetime
import time
import os

app = FastAPI(title="CSAO Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA & MODEL
# ─────────────────────────────────────────────────────────────────────────────
print("Loading data...")
users = pd.read_csv("users.csv")
rests = pd.read_csv("restaurants.csv")
menu  = pd.read_csv("menu_items.csv")
orders = pd.read_csv("order_history.csv")
csao = pd.read_csv("csao_interactions.csv")

print("Loading models...")
model = lgb.Booster(model_file="csao_model.txt")

item2vec_model = None
try:
    from gensim.models import Word2Vec
    if os.path.exists("item2vec.model"):
        item2vec_model = Word2Vec.load("item2vec.model")
except Exception as e:
    print(f"Warning: Item2Vec could not be loaded: {e}")

print("Building dictionaries...")
cooc = defaultdict(lambda: defaultdict(int))
for _, row in orders.iterrows():
    items_str = str(row.get("items_ordered", ""))
    items = [x.strip() for x in items_str.split(",") if x.strip()]
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            cooc[items[i]][items[j]] += 1
            cooc[items[j]][items[i]] += 1
cooc = dict(cooc)

le_map = {}
for col in ["user_segment", "meal_time", "hexagon_node", "candidate_category",
            "anchor_cuisine", "candidate_cuisine", "city_tier", "price_range"]:
    if col in csao.columns:
        le = LabelEncoder()
        le.fit(csao[col].astype(str))
        le_map[col] = le

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
# API MODELS
# ─────────────────────────────────────────────────────────────────────────────
class ProfileRequest(BaseModel):
    segment: str
    is_veg: bool
    city: str
    meal_time: str

class RecommendRequest(BaseModel):
    restaurant_id: str
    cart_item_ids: List[str]
    profile: ProfileRequest

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (Copied from app.py)
# ─────────────────────────────────────────────────────────────────────────────
def generate_candidates(restaurant_id, cart_item_ids, user_row, meal_time, hour):
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

    log_lines.append(f'Generated for {len(cart_item_ids)} items with AOV {aov}')

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
            if len(pool) >= n: return rank_by_similarity(pool, n)
            pool = rest_menu[rest_menu["category"] == category]
            return rank_by_similarity(pool, n)
        else:
            pool = rest_menu[rest_menu["category"] == category]
            return rank_by_similarity(pool, n)

    used_ids = set(cart_item_ids)

    # Note: Shortened Hexagon Generator slightly for API length but preserving identical core logic
    n1 = get_cuisine_pool("Extension", 2)
    for _, r in n1[~n1["item_id"].isin(used_ids)].iterrows():
        add_candidate(r, "Node1_Extension", r.get("sim_score")); used_ids.add(r["item_id"])

    n2 = get_cuisine_pool("Side", 2)
    for _, r in n2[~n2["item_id"].isin(used_ids)].iterrows():
        add_candidate(r, "Node2_Texture", r.get("sim_score")); used_ids.add(r["item_id"])

    # Co-occurrence
    cooc_scores = defaultdict(int)
    for cid in cart_item_ids:
        for co_id, cnt in cooc.get(cid, {}).items():
            if co_id not in used_ids: cooc_scores[co_id] += cnt
    cooc_rest = rest_menu[rest_menu["item_id"].isin(cooc_scores.keys())]
    cooc_same = cooc_rest[cooc_rest["cuisine"] == anchor_cuisine]
    n3 = rank_by_similarity(cooc_same if len(cooc_same) >= 2 else cooc_rest, 2)
    for _, r in n3[~n3["item_id"].isin(used_ids)].iterrows():
        add_candidate(r, "Node3_CoOccurrence", r.get("sim_score")); used_ids.add(r["item_id"])

    n4 = rank_by_similarity(rest_menu[(rest_menu["category"] == "Beverage") & (~rest_menu["item_id"].isin(used_ids))], 2)
    for _, r in n4.iterrows(): add_candidate(r, "Node4_Beverage", r.get("sim_score")); used_ids.add(r["item_id"])

    n5 = rank_by_similarity(rest_menu[(rest_menu["category"] == "Dessert") & (~rest_menu["item_id"].isin(used_ids))], 2)
    for _, r in n5.iterrows(): add_candidate(r, "Node5_Dessert", r.get("sim_score")); used_ids.add(r["item_id"])

    n6 = rank_by_similarity(rest_menu[(rest_menu["price"] <= max(headroom * 0.5, 50)) & (~rest_menu["category"].isin(["Main", "Beverage", "Dessert"])) & (~rest_menu["item_id"].isin(used_ids))], 2)
    for _, r in n6.iterrows(): add_candidate(r, "Node6_BudgetHabit", r.get("sim_score")); used_ids.add(r["item_id"])

    unique_candidates = {c["item_id"]: c for c in candidates}.values()
    candidates = list(unique_candidates)

    if not candidates: return pd.DataFrame(), log_lines

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
    cdf["affinity_match"] = np.where(cdf["category"]=="Beverage", cdf["beverage_affinity"], np.where(cdf["category"]=="Dessert", cdf["dessert_affinity"], 0.5))
    cdf["price_match"] = (cdf["candidate_is_veg"] == int(user_row["is_veg"])).astype(int)
    cdf["budget_safe"] = (cdf["candidate_price"] <= headroom * 0.4).astype(int)
    cdf["is_beverage"] = (cdf["category"] == "Beverage").astype(int)
    cdf["is_dessert"] = (cdf["category"] == "Dessert").astype(int)
    cdf["is_extension"] = (cdf["category"] == "Extension").astype(int)

    rest_info = rests[rests["restaurant_id"] == restaurant_id].iloc[0]
    cdf["avg_rating"] = rest_info["avg_rating"]
    cdf["is_chain"] = int(rest_info["is_chain"])
    cdf["price_range"] = rest_info["price_range"]

    for col in le_map:
        if col in cdf.columns:
            try: cdf[col + "_enc"] = le_map[col].transform(cdf[col].astype(str))
            except ValueError: cdf[col + "_enc"] = 0

    return cdf, log_lines

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/restaurants")
def get_restaurants():
    """Return list of distinct restaurants."""
    r = rests[["restaurant_id", "name"]].drop_duplicates().to_dict("records")
    return r

@app.get("/api/menu/{restaurant_id}")
def get_menu(restaurant_id: str):
    """Return menu items for a specific restaurant."""
    m = menu[menu["restaurant_id"] == restaurant_id][["item_id", "item_name", "price", "is_veg"]].to_dict("records")
    return m

@app.post("/api/recommend")
def get_recommendations(req: RecommendRequest):
    if not req.cart_item_ids:
        return {"recommendations": []}

    matching = users[(users["city"] == req.profile.city) & 
                     (users["user_segment"] == req.profile.segment) & 
                     (users["is_veg"] == req.profile.is_veg)]
    
    if len(matching) > 0:
        user_row = matching.iloc[0]
    else:
        city_m = users[users["city"] == req.profile.city]
        user_row = city_m.iloc[0] if len(city_m) > 0 else users.iloc[0]

    hour_map = {"breakfast": 9, "lunch": 13, "evening_snack": 17, "dinner": 20, "late_night": 23}
    hour = hour_map.get(req.profile.meal_time, 20)

    cdf, _ = generate_candidates(req.restaurant_id, req.cart_item_ids, user_row, req.profile.meal_time, hour)

    if len(cdf) == 0:
        return {"recommendations": []}

    X_demo = cdf[[f for f in FEATURES if f in cdf.columns]].fillna(0)
    for f in FEATURES:
        if f not in X_demo.columns: X_demo[f] = 0
    X_demo = X_demo[FEATURES]

    cdf["score"] = model.predict(X_demo)
    cdf = cdf.sort_values("score", ascending=False).reset_index(drop=True)
    
    top_recs = cdf.nlargest(5, "score").to_dict("records")

    cart_value = menu[menu["item_id"].isin(req.cart_item_ids)]["price"].sum()
    headroom = max(0, user_row["historical_aov"] - cart_value)

    return {
        "user_aov": float(user_row["historical_aov"]),
        "cart_value": float(cart_value),
        "headroom": float(headroom),
        "recommendations": top_recs
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
