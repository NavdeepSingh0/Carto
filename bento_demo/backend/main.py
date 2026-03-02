from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from collections import defaultdict
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
import os
import time

app = FastAPI(title="Zomato CSAO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA & MODEL
# ─────────────────────────────────────────────────────────────────────────────
print("Loading Real Data from Datasets...")
# Support both local dev (relative path) and Render deployment (env var override)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(_SCRIPT_DIR, "../../datasets/"))
MODEL_DIR = os.environ.get("MODEL_DIR", os.path.join(_SCRIPT_DIR, "../../model_artifacts/"))

users = pd.read_csv(os.path.join(DATA_DIR, "users.csv"))
rests = pd.read_csv(os.path.join(DATA_DIR, "restaurants.csv"))
menu = pd.read_csv(os.path.join(DATA_DIR, "menu_items.csv"))
orders = pd.read_csv(os.path.join(DATA_DIR, "order_history.csv"))
csao = pd.read_csv(os.path.join(DATA_DIR, "csao_interactions.csv"))

# Load extension parent mapping (Extra Pav → Pav Bhaji/Vada Pav, Salan → Biryani, etc.)
ext_map_path = os.path.join(DATA_DIR, "extension_mappings.csv")
if os.path.exists(ext_map_path):
    ext_map = pd.read_csv(ext_map_path)
    EXTENSION_PARENTS = ext_map.groupby("extension_global_id")["parent_global_id"].apply(set).to_dict()
    print(f"Extension mappings loaded: {len(EXTENSION_PARENTS)} extensions mapped")
else:
    EXTENSION_PARENTS = {}
    print("Warning: extension_mappings.csv not found, Node1 will run unfiltered")

print("Loading Real Models...")
model = lgb.Booster(model_file=os.path.join(MODEL_DIR, "csao_model.txt"))

item2vec_model = None
try:
    from gensim.models import Word2Vec
    if os.path.exists(os.path.join(MODEL_DIR, "item2vec.model")):
        item2vec_model = Word2Vec.load(os.path.join(MODEL_DIR, "item2vec.model"))
except Exception as e:
    print(f"Warning: Item2Vec could not be loaded: {e}")

print("Building co-occurrence & user history dictionaries...")
cooc = defaultdict(lambda: defaultdict(int))
for _, row in orders.iterrows():
    items_str = str(row.get("items_ordered", ""))
    items = [x.strip() for x in items_str.split(",") if x.strip()]
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            cooc[items[i]][items[j]] += 1
            cooc[items[j]][items[i]] += 1
cooc = dict(cooc)

# Build user → set(ordered item_ids) map for user_ordered_this_before feature
# orders.items_ordered is comma-separated item IDs
user_history_map = defaultdict(set)
for _, row in orders.iterrows():
    uid = row.get("user_id", "")
    items_str = str(row.get("items_ordered", ""))
    for iid in [x.strip() for x in items_str.split(",") if x.strip()]:
        user_history_map[uid].add(iid)
user_history_map = dict(user_history_map)

le_map = {}
for col in ["user_segment", "meal_time", "hexagon_node", "candidate_category",
            "anchor_cuisine", "candidate_cuisine", "city_tier", "price_range"]:
    if col in csao.columns:
        le = LabelEncoder()
        le.fit(csao[col].astype(str))
        le_map[col] = le

max_awo = menu["avg_weekly_orders"].max()

CATEGORY_CUISINES = {"Beverage", "Dessert"}

# FEATURES must exactly match the 33 features the csao_model.txt was trained on.
# NOTE: In Iteration 3 of our solution (solution_context.md), we retrained on Kaggle
# WITHOUT hexagon_node_enc and is_hexagon_candidate to eliminate data leakage (AUC 1.0).
# The model artifact here reflects the final CLEAN Kaggle run (AUC 0.7741).
# user_ordered_this_before is computed at runtime and used in post-model score boosting.
FEATURES = [
    "hexagon_node_enc", "is_hexagon_candidate",   # kept for model compat; zero-weighted post-leakage-fix
    "user_historical_aov", "user_segment_enc", "price_sensitivity",
    "dessert_affinity", "beverage_affinity", "total_orders_lifetime",
    "user_item_affinity", "user_cuisine_affinity", "affinity_match",
    "cart_value", "n_items_in_cart", "embedding_variance", "is_chaos_cart", "anchor_cuisine_enc",
    "candidate_price", "price_ratio", "aov_headroom", "price_match", "budget_safe",
    "candidate_category_enc", "candidate_is_veg", "item_popularity_score",
    "hour_of_day", "day_of_week", "meal_time_enc", "city_tier_enc",
    "avg_rating", "is_chain",
    "is_beverage", "is_dessert", "is_extension",
]

print("Server ready!")


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
# ANCHOR CUISINE LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def get_anchor_cuisine(cart_items_info):
    real_cuisine_items = cart_items_info[~cart_items_info["cuisine"].isin(CATEGORY_CUISINES)]
    if len(real_cuisine_items) > 0:
        return real_cuisine_items["cuisine"].mode().iloc[0]
    if len(cart_items_info) > 0:
        rest_id = cart_items_info["restaurant_id"].iloc[0]
        rest_items = menu[(menu["restaurant_id"] == rest_id) & (~menu["cuisine"].isin(CATEGORY_CUISINES))]
        if len(rest_items) > 0:
            return rest_items["cuisine"].mode().iloc[0]
    return "North Indian"


# ─────────────────────────────────────────────────────────────────────────────
# HEXAGON CANDIDATE GENERATOR (identical to legacy Streamlit app.py)
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
    anchor_cuisine = get_anchor_cuisine(cart_items_info)
    cart_value = cart_items_info["price"].sum()
    n_items = len(cart_item_ids)

    real_cuisines = cart_items_info[~cart_items_info["cuisine"].isin(CATEGORY_CUISINES)]["cuisine"].nunique()
    cuisines_in_cart = max(real_cuisines, 1)

    # Real embedding_variance from Item2Vec vectors (Chaos Cart trigger)
    # Per solution_context.md: variance of item vectors detects cross-cuisine chaos
    if item2vec_model is not None and len(cart_item_ids) >= 2:
        cart_vecs_ev = [item2vec_model.wv[iid] for iid in cart_item_ids
                        if iid in item2vec_model.wv]
        if len(cart_vecs_ev) >= 2:
            embedding_variance = float(np.var(np.array(cart_vecs_ev), axis=0).mean())
        else:
            embedding_variance = float(cuisines_in_cart * 0.1)
    else:
        embedding_variance = float(cuisines_in_cart * 0.1)
    # Chaos threshold τ tuned on historical data (see solution_context.md Edge Case 2)
    CHAOS_THRESHOLD = 0.25
    is_chaos = 1 if embedding_variance >= CHAOS_THRESHOLD else 0
    aov = user_row["historical_aov"]
    headroom = max(0, aov - cart_value)

    cart_categories = set(cart_items_info["category"].tolist()) if len(cart_items_info) > 0 else set()

    # ── Engine Log Header ──
    log_lines.append("═══════════════════════════════════════════════")
    log_lines.append("  HEXAGON CANDIDATE GENERATOR — ENGINE LOG")
    log_lines.append("═══════════════════════════════════════════════")
    log_lines.append(f"  Anchor Cuisine: {anchor_cuisine}")
    log_lines.append(f"  Cart Value: ₹{cart_value:.0f}  |  Items: {n_items}  |  AOV: ₹{aov:.0f}")
    log_lines.append(f"  Headroom: ₹{headroom:.0f}  |  Chaos Cart: {'YES ⚡' if is_chaos else 'No'}")
    log_lines.append(f"  Embedding Variance: {embedding_variance:.4f}  (τ = 0.25)")
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
            if len(pool) >= n: return rank_by_similarity(pool, n)
            pool = rest_menu[rest_menu["category"] == category]
            return rank_by_similarity(pool, n)
        else:
            pool = rest_menu[rest_menu["category"] == category]
            return rank_by_similarity(pool, n)

    used_ids = set(cart_item_ids)

    # Compute cart global IDs once — used by Node1 filter AND global extension filter
    cart_global_ids = set(cart_items_info["global_item_id"].tolist()) if "global_item_id" in cart_items_info.columns else set()

    # Node 1: Extension (filtered by parent mapping)
    # Pull more initial candidates so we have room to filter
    n1_raw = get_cuisine_pool("Extension", 10)
    n1_raw = n1_raw[~n1_raw["item_id"].isin(used_ids)]

    # Filter: only keep extensions whose parent dish is in the cart
    valid_n1 = []
    skipped_n1 = []
    for _, r in n1_raw.iterrows():
        ext_gid = r.get("global_item_id", "")
        required_parents = EXTENSION_PARENTS.get(ext_gid, set())
        if not required_parents:
            # No mapping exists — unmapped extension, allow as fallback
            valid_n1.append(r)
        elif required_parents.intersection(cart_global_ids):
            # Parent dish IS in cart — this extension makes sense
            valid_n1.append(r)
        else:
            # Parent dish NOT in cart — skip (this is the "Extra Pav with Kulfi" fix)
            skipped_n1.append(r.get("item_name", ext_gid))
        if len(valid_n1) >= 2:
            break

    n1 = pd.DataFrame(valid_n1) if valid_n1 else pd.DataFrame()
    for _, r in n1.iterrows():
        add_candidate(r, "Node1_Extension", r.get("sim_score")); used_ids.add(r["item_id"])
    log_lines.append(f"  Node1 Extension: {len(n1)} candidates (parent-mapped + Item2Vec)")
    for _, r in n1.iterrows():
        log_lines.append(f"    → {r['item_name']} (sim: {r.get('sim_score', 0):.2f})")
    if skipped_n1:
        log_lines.append(f"    ✗ Filtered out (no parent in cart): {', '.join(skipped_n1)}")

    # Node 2: Texture/Side
    n2 = get_cuisine_pool("Side", 2)
    n2 = n2[~n2["item_id"].isin(used_ids)]
    for _, r in n2.iterrows():
        add_candidate(r, "Node2_Texture", r.get("sim_score")); used_ids.add(r["item_id"])
    log_lines.append(f"  Node2 Texture:   {len(n2)} candidates (cuisine-matched + Item2Vec)")
    for _, r in n2.iterrows():
        log_lines.append(f"    → {r['item_name']} (sim: {r.get('sim_score', 0):.2f})")

    # Node 3: Co-occurrence
    cooc_scores = defaultdict(int)
    for cid in cart_item_ids:
        for co_id, cnt in cooc.get(cid, {}).items():
            if co_id not in used_ids: cooc_scores[co_id] += cnt
    cooc_rest = rest_menu[rest_menu["item_id"].isin(cooc_scores.keys())]
    cooc_same = cooc_rest[cooc_rest["cuisine"] == anchor_cuisine]
    n3 = rank_by_similarity(cooc_same if len(cooc_same) >= 2 else cooc_rest, 2)
    n3 = n3[~n3["item_id"].isin(used_ids)]
    for _, r in n3.iterrows():
        add_candidate(r, "Node3_CoOccurrence", r.get("sim_score")); used_ids.add(r["item_id"])
    log_lines.append(f"  Node3 CoOccur:   {len(n3)} candidates (co-purchase + cuisine filter)")
    for _, r in n3.iterrows():
        log_lines.append(f"    → {r['item_name']} (sim: {r.get('sim_score', 0):.2f})")

    # Node 4: Beverage
    bev_count = 1 if "Beverage" in cart_categories else 2
    n4 = rank_by_similarity(rest_menu[(rest_menu["category"] == "Beverage") & (~rest_menu["item_id"].isin(used_ids))], bev_count)
    for _, r in n4.iterrows():
        add_candidate(r, "Node4_Beverage", r.get("sim_score")); used_ids.add(r["item_id"])
    log_lines.append(f"  Node4 Beverage:  {len(n4)} candidates (Item2Vec ranked)")
    for _, r in n4.iterrows():
        log_lines.append(f"    → {r['item_name']} (sim: {r.get('sim_score', 0):.2f})")

    # Node 5: Dessert
    des_count = 1 if "Dessert" in cart_categories else 2
    n5 = rank_by_similarity(rest_menu[(rest_menu["category"] == "Dessert") & (~rest_menu["item_id"].isin(used_ids))], des_count)
    for _, r in n5.iterrows():
        add_candidate(r, "Node5_Dessert", r.get("sim_score")); used_ids.add(r["item_id"])
    log_lines.append(f"  Node5 Dessert:   {len(n5)} candidates (Item2Vec ranked)")
    for _, r in n5.iterrows():
        log_lines.append(f"    → {r['item_name']} (sim: {r.get('sim_score', 0):.2f})")

    # Node 6: Budget/Habit
    n6 = rank_by_similarity(rest_menu[(rest_menu["price"] <= max(headroom * 0.5, 50)) &
                                       (~rest_menu["category"].isin(["Main", "Beverage", "Dessert"])) &
                                       (~rest_menu["item_id"].isin(used_ids))], 2)
    for _, r in n6.iterrows():
        add_candidate(r, "Node6_BudgetHabit", r.get("sim_score")); used_ids.add(r["item_id"])
    log_lines.append(f"  Node6 Budget:    {len(n6)} candidates (within ₹{max(headroom*0.5, 50):.0f} + Item2Vec)")
    for _, r in n6.iterrows():
        log_lines.append(f"    → {r['item_name']} (sim: {r.get('sim_score', 0):.2f})")

    log_lines.append("")
    log_lines.append(f"  Total candidates generated: {len(candidates)}")

    # Deduplicate
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c["item_id"] not in seen:
            seen.add(c["item_id"])
            unique_candidates.append(c)
    candidates = unique_candidates

    # ── Global Extension Parent Filter ──────────────────────────────────
    # Remove ANY extension candidate whose parent dish is not in the cart.
    # This catches extensions that leaked in via Node3 (co-occurrence) or
    # Node6 (budget), not just Node1. One filter to rule them all.
    pre_filter_count = len(candidates)
    filtered_candidates = []
    ext_filtered_names = []
    for c in candidates:
        if c["category"] == "Extension":
            ext_gid_arr = menu[menu["item_id"] == c["item_id"]]["global_item_id"].values
            if len(ext_gid_arr) > 0:
                ext_gid = ext_gid_arr[0]
                required_parents = EXTENSION_PARENTS.get(ext_gid, set())
                if required_parents and not required_parents.intersection(cart_global_ids):
                    ext_filtered_names.append(c["item_name"])
                    continue  # skip — no valid parent in cart
        filtered_candidates.append(c)
    candidates = filtered_candidates
    if ext_filtered_names:
        log_lines.append(f"  ⚡ Global ext filter removed {len(ext_filtered_names)}: {', '.join(ext_filtered_names)}")
        log_lines.append(f"  Candidates after filter: {len(candidates)} (was {pre_filter_count})")

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
    cdf["item_popularity_score"] = np.clip(base_pop + np.random.normal(0, 0.05, len(cdf)), 0, 1)
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

    # user_ordered_this_before: has this user ordered this specific item before?
    # Per solution_context.md: "single fastest way to drag an F1 score out of the 30s"
    user_hist = user_history_map.get(str(user_row.get("user_id", "")), set())
    cdf["user_ordered_this_before"] = cdf["item_id"].isin(user_hist).astype(int)

    # user_item_affinity: fraction of this user's orders that included this item
    # A non-zero, user-specific signal rather than a flat constant
    total_user_orders = max(user_row.get("total_orders_lifetime", 20), 1)
    cdf["user_item_affinity"] = (
        cdf["user_ordered_this_before"] * 0.3  # known favourite gets a 30% signal
        + (1 - cdf["user_ordered_this_before"]) * (cdf["item_popularity_score"] * 0.049)
    )

    rest_info = rests[rests["restaurant_id"] == restaurant_id].iloc[0]
    cdf["avg_rating"] = rest_info["avg_rating"]
    cdf["is_chain"] = int(rest_info["is_chain"])
    cdf["price_range"] = rest_info["price_range"]

    for col in le_map:
        if col in cdf.columns:
            try: cdf[col + "_enc"] = le_map[col].transform(cdf[col].astype(str))
            except ValueError: cdf[col + "_enc"] = 0

    return cdf, log_lines


def diversify_top_k(cdf, k=5, cart_categories=None):
    if cart_categories is None:
        cart_categories = set()
    sorted_df = cdf.sort_values("final_score", ascending=False)
    selected = []
    category_counts = defaultdict(int)
    for _, row in sorted_df.iterrows():
        cat = row["category"]
        max_per_cat = 1 if cat in cart_categories else 2
        if category_counts[cat] < max_per_cat:
            selected.append(row)
            category_counts[cat] += 1
        if len(selected) >= k:
            break
    if len(selected) < k:
        selected_ids = {r["item_id"] for r in selected}
        for _, row in sorted_df.iterrows():
            if row["item_id"] not in selected_ids:
                selected.append(row)
                if len(selected) >= k:
                    break
    return pd.DataFrame(selected)


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/cities")
def get_cities():
    """Return list of available cities."""
    cities = sorted(rests["city"].unique().tolist())
    return cities


@app.get("/api/restaurants")
def get_restaurants(city: Optional[str] = None):
    """Return restaurants, optionally filtered by city. Includes cuisine label."""
    df = rests.copy()
    if city:
        df = df[df["city"] == city]
    result = []
    for _, r in df.iterrows():
        result.append({
            "restaurant_id": r["restaurant_id"],
            "name": r["name"],
            "city": r["city"],
            "cuisine_primary": r["cuisine_primary"],
            "avg_rating": float(r["avg_rating"]),
            "price_range": r["price_range"],
            "is_chain": bool(r["is_chain"]),
        })
    return result


@app.get("/api/menu/{restaurant_id}")
def get_menu(restaurant_id: str):
    """Return menu items for a restaurant, including category and cuisine."""
    m = menu[menu["restaurant_id"] == restaurant_id][
        ["item_id", "item_name", "price", "is_veg", "category", "cuisine"]
    ].to_dict("records")
    return m


@app.get("/api/profiles")
def get_profiles():
    """Return sample user profiles for the demo."""
    profiles = []
    # Get a sample user per city × segment combo for demo
    for city in sorted(rests["city"].unique()):
        city_users = users[users["city"] == city]
        for segment in ["budget", "mid", "premium"]:
            seg_users = city_users[city_users["user_segment"] == segment]
            if len(seg_users) > 0:
                u = seg_users.iloc[0]
                profiles.append({
                    "user_id": u["user_id"],
                    "name": u.get("name", f"{segment.title()} User"),
                    "city": city,
                    "segment": segment,
                    "is_veg": bool(u["is_veg"]),
                    "historical_aov": float(u["historical_aov"]),
                })
    return profiles


@app.post("/api/recommend")
def get_recommendations(req: RecommendRequest):
    if not req.cart_item_ids:
        return {"recommendations": [], "user_aov": 450, "cart_value": 0, "headroom": 450, "engine_log": []}

    matching = users[(users["city"] == req.profile.city) &
                     (users["user_segment"] == req.profile.segment) &
                     (users["is_veg"] == req.profile.is_veg)]

    if len(matching) > 0:
        user_row = matching.iloc[0]
    else:
        city_m = users[users["city"] == req.profile.city]
        user_row = city_m.iloc[0] if len(city_m) > 0 else users.iloc[0]

    hour_map = {"breakfast": 9, "lunch": 13, "evening_snack": 17, "snacks": 17, "dinner": 20, "late_night": 23}
    hour = hour_map.get(req.profile.meal_time, 20)

    t0 = time.time()
    cdf, log_lines = generate_candidates(req.restaurant_id, req.cart_item_ids, user_row, req.profile.meal_time, hour)
    t_gen = time.time() - t0

    cart_items_info = menu[menu["item_id"].isin(req.cart_item_ids)]
    cart_value = cart_items_info["price"].sum()
    headroom = max(0, user_row["historical_aov"] - cart_value)
    cart_categories = set(cart_items_info["category"].tolist())

    if len(cdf) == 0:
        return {
            "recommendations": [],
            "user_aov": float(user_row["historical_aov"]),
            "cart_value": float(cart_value),
            "headroom": float(headroom),
            "engine_log": log_lines,
        }

    X_demo = cdf[[f for f in FEATURES if f in cdf.columns]].fillna(0)
    for f in FEATURES:
        if f not in X_demo.columns: X_demo[f] = 0
    X_demo = X_demo[FEATURES]

    t1 = time.time()
    cdf["lgb_score"] = model.predict(X_demo)
    t_pred = time.time() - t1
    t_total = (t_gen + t_pred) * 1000

    # Post-model boosting
    anchor_cuisine = get_anchor_cuisine(cart_items_info)
    cuisine_boost = np.where(
        cdf["cuisine"] == anchor_cuisine, 0.08,
        np.where(cdf["cuisine"].isin(CATEGORY_CUISINES), 0.0, -0.03)
    )
    gap_boost = np.where(~cdf["category"].isin(cart_categories), 0.05, -0.02)
    meal_boost = np.zeros(len(cdf))
    if "Beverage" not in cart_categories:
        meal_boost = np.where(cdf["category"] == "Beverage", 0.04, meal_boost)
    if "Dessert" not in cart_categories:
        meal_boost = np.where(cdf["category"] == "Dessert", 0.03, meal_boost)
    budget_penalty = np.where(cdf["candidate_price"] > headroom * 0.7, -0.04, 0.0) if headroom > 0 else np.zeros(len(cdf))

    # user_ordered_this_before boost — per solution_context.md Iteration 3:
    # "the single fastest way to drag an F1 score" — items previously ordered by the user surface first
    history_boost = np.where(cdf["user_ordered_this_before"] == 1, 0.12, 0.0)

    cdf["final_score"] = cdf["lgb_score"] + cuisine_boost + gap_boost + meal_boost + budget_penalty + history_boost
    cdf["score"] = cdf["final_score"]

    cdf = cdf.sort_values("score", ascending=False).reset_index(drop=True)

    # ── Scoring section in engine log ──
    log_lines.append("")
    log_lines.append("═══════════════════════════════════════════════")
    log_lines.append("  LIGHTGBM RANKER — SCORING")
    log_lines.append("═══════════════════════════════════════════════")
    log_lines.append(f"  Features used: {len(FEATURES)} (+ post-model boosts)")
    log_lines.append(f"  Candidates scored: {len(cdf)}")
    history_boosted = int(cdf["user_ordered_this_before"].sum())
    if history_boosted > 0:
        log_lines.append(f"  History boost (+0.12): {history_boosted} item(s) user has ordered before")
    if len(cdf) > 0:
        log_lines.append(f"  Top score: {cdf.iloc[0]['score']:.4f} ({cdf.iloc[0]['item_name']} — {cdf.iloc[0]['hexagon_node']})")
    log_lines.append(f"  Inference time: {t_pred*1000:.1f}ms")
    log_lines.append("")
    log_lines.append("═══════════════════════════════════════════════")
    log_lines.append("  PERFORMANCE")
    log_lines.append("═══════════════════════════════════════════════")
    log_lines.append(f"  Candidate generation: {t_gen*1000:.1f}ms")
    log_lines.append(f"  LightGBM inference:   {t_pred*1000:.1f}ms")
    latency_status = "✅ PASS (<300ms)" if t_total < 300 else "⚠️ SLOW"
    log_lines.append(f"  Total latency:        {t_total:.1f}ms  {latency_status}")

    # Apply diversity
    top_recs_df = diversify_top_k(cdf, k=5, cart_categories=cart_categories)
    top_recs_df = top_recs_df.sort_values("final_score", ascending=False)

    recs_list = []
    for _, r in top_recs_df.iterrows():
        recs_list.append({
            "item_id": r["item_id"],
            "item_name": r["item_name"],
            "price": float(r["price"]),
            "is_veg": bool(r["is_veg"]),
            "hexagon_node": r["hexagon_node"],
            "score": float(r["final_score"]),
            "category": r["category"],
            "cuisine": r.get("cuisine", ""),
            "sim_score": float(r.get("sim_score", 0)) if r.get("sim_score") is not None else 0.0,
        })

    return {
        "user_aov": float(user_row["historical_aov"]),
        "cart_value": float(cart_value),
        "headroom": float(headroom),
        "recommendations": recs_list,
        "engine_log": log_lines,
        "latency_ms": round(t_total, 1),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
