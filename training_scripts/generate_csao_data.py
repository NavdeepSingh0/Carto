"""
CSAO Synthetic Dataset Generator v2.0
======================================
Generates 5 interconnected CSVs for a Zomato-like CSAO (Cart Super Add-On)
recommendation system. Designed to be realistic, internally consistent,
and free of data leakage in the was_added label.

Target Metrics (matching/exceeding reference):
  - Total CSAO sessions: ~3,000 (from 25,000 orders)
  - Total CSAO rows:     ~24,000
  - Acceptance rate:     ~40-46%
  - Node hierarchy:      Node1 > Node3 > Node4 > Node2 > Node5 > Node6 > Noise
  - AUC target:          0.65-0.75 (realistic, not inflated)
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from collections import defaultdict

# ── Reproducibility ────────────────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — ONTOLOGY & CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# (global_item_id, cuisine, category, is_veg, min_price, max_price)
ONTOLOGY = [
    # South Indian
    ("IDLI",             "South Indian", "Main",      True,  40,  100),
    ("DOSA",             "South Indian", "Main",      True,  80,  200),
    ("MEDU_VADA",        "South Indian", "Side",      True,  50,  100),
    ("UTTAPAM",          "South Indian", "Main",      True, 100,  220),
    ("SAMBAR",           "South Indian", "Extension", True,  30,   60),
    ("COCONUT_CHUTNEY",  "South Indian", "Extension", True,  20,   40),
    ("RASAM",            "South Indian", "Extension", True,  40,   90),
    ("FILTER_COFFEE",    "South Indian", "Beverage",  True,  40,   90),
    ("PAYASAM",          "South Indian", "Dessert",   True,  80,  180),
    # North Indian
    ("CHOLE_BHATURE",    "North Indian", "Main",      True, 120,  280),
    ("EXTRA_BHATURA",    "North Indian", "Extension", True,  40,   80),
    ("BUTTER_NAAN",      "North Indian", "Side",      True,  40,   90),
    ("PANEER_BUTTER_MASALA","North Indian","Main",    True, 180,  380),
    ("DAL_MAKHANI",      "North Indian", "Main",      True, 150,  350),
    ("MASALA_PAPAD",     "North Indian", "Side",      True,  30,   80),
    ("RAITA",            "North Indian", "Extension", True,  40,   90),
    ("BOONDI_RAITA",     "North Indian", "Side",      True,  50,  100),
    ("GULAB_JAMUN",      "North Indian", "Dessert",   True,  50,  150),
    ("KHEER",            "North Indian", "Dessert",   True,  80,  200),
    # Indian Street
    ("PAV_BHAJI",        "Indian Street","Main",      True, 100,  250),
    ("EXTRA_PAV",        "Indian Street","Extension", True,  20,   40),
    ("MASALA_PAV",       "Indian Street","Side",      True,  40,   80),
    ("VADA_PAV",         "Indian Street","Main",      True,  40,   80),
    # Biryani
    ("VEG_BIRYANI",      "Biryani",      "Main",      True, 180,  350),
    ("CHICKEN_BIRYANI",  "Biryani",      "Main",      False,220,  400),
    ("MUTTON_BIRYANI",   "Biryani",      "Main",      False,270,  450),
    ("SALAN",            "Biryani",      "Extension", True,  30,   80),
    # Mughlai
    ("BUTTER_CHICKEN",   "Mughlai",      "Main",      False,200,  400),
    ("NAAN",             "Mughlai",      "Side",      True,  40,   80),
    ("SEEKH_KEBAB",      "Mughlai",      "Side",      False,150,  320),
    # Chinese
    ("VEG_FRIED_RICE",   "Chinese",      "Main",      True, 150,  300),
    ("CHICKEN_FRIED_RICE","Chinese",     "Main",      False,180,  350),
    ("VEG_MANCHURIAN",   "Chinese",      "Main",      True, 160,  320),
    ("HAKKA_NOODLES",    "Chinese",      "Main",      True, 150,  320),
    ("SPRING_ROLLS",     "Chinese",      "Side",      True, 120,  250),
    ("HOT_SOUR_SOUP",    "Chinese",      "Beverage",  True, 100,  200),
    # Continental
    ("MARGHERITA_PIZZA", "Continental",  "Main",      True, 200,  400),
    ("PASTA_ARRABBIATA", "Continental",  "Main",      True, 200,  400),
    ("GARLIC_BREAD",     "Continental",  "Side",      True, 100,  250),
    ("FRENCH_FRIES",     "Continental",  "Side",      True,  80,  200),
    ("TIRAMISU",         "Continental",  "Dessert",   True, 150,  350),
    ("CAESAR_SALAD",     "Continental",  "Side",      False,180,  350),
    # Beverages (cross-cuisine)
    ("MASALA_CHAAS",     "Beverage",     "Beverage",  True,  40,   90),
    ("LASSI",            "Beverage",     "Beverage",  True,  60,  120),
    ("MANGO_LASSI",      "Beverage",     "Beverage",  True,  80,  180),
    ("COLD_COFFEE",      "Beverage",     "Beverage",  True, 100,  250),
    ("VIRGIN_MOJITO",    "Beverage",     "Beverage",  True, 100,  200),
    # Desserts (cross-cuisine)
    ("SHRIKHAND",        "Dessert",      "Dessert",   True,  80,  200),
    ("KULFI",            "Dessert",      "Dessert",   True,  60,  150),
    ("BROWNIE",          "Dessert",      "Dessert",   True,  80,  250),
    ("CHOCO_LAVA_CAKE",  "Dessert",      "Dessert",   True,  90,  200),
]

ONT_DF = pd.DataFrame(
    ONTOLOGY,
    columns=["global_item_id", "cuisine", "category", "is_veg", "min_p", "max_p"]
)

# Which Hexagon node does a category map to for positive candidates?
CATEGORY_TO_NODE = {
    "Extension": "Node1_Extension",
    "Side":      "Node2_Texture",
    "Main":      "Node3_CoOccurrence",
    "Beverage":  "Node4_Beverage",
    "Dessert":   "Node5_Dessert",
}

# Node acceptance probability for non-ground-truth (probabilistic) candidates
NODE_ACCEPT_PROB = {
    "Node1_Extension":    0.72,
    "Node3_CoOccurrence": 0.55,
    "Node4_Beverage":     0.50,
    "Node2_Texture":      0.42,
    "Node5_Dessert":      0.35,
    "Node6_BudgetHabit":  0.28,
    "Noise":              0.10,
}

CITY_CONFIG = [
    # name, tier, veg_prob, pincode_prefix, cuisine_weights
    ("Mumbai",    "Tier1", 0.40, "400"),
    ("Delhi",     "Tier1", 0.40, "110"),
    ("Bangalore", "Tier1", 0.38, "560"),
    ("Hyderabad", "Tier1", 0.30, "500"),
    ("Pune",      "Tier1", 0.42, "411"),
    ("Surat",     "Tier2", 0.60, "395"),
    ("Jaipur",    "Tier2", 0.65, "302"),
    ("Lucknow",   "Tier2", 0.38, "226"),
    ("Chandigarh","Tier2", 0.45, "160"),
    ("Kochi",     "Tier2", 0.25, "682"),
]

CUISINES = ["South Indian", "North Indian", "Indian Street", "Chinese",
            "Continental", "Mughlai", "Biryani"]

MEAL_HOURS = {
    "breakfast":    (7,  10),
    "lunch":        (12, 15),
    "dinner":       (19, 22),
    "evening_snack":(16, 18),
    "late_night":   (23, 23),
}

FIRST_M  = ["Aarav","Vihaan","Aryan","Rohan","Rishi","Aditya","Kabir","Arjun",
             "Sai","Rahul","Amit","Vikram","Suresh","Ramesh","Ishaan"]
FIRST_F  = ["Saanvi","Aadya","Kiara","Prisha","Ananya","Avni","Kavya","Neha",
             "Pooja","Priya","Riya","Sneha","Diya","Myra","Sunita"]
LAST     = ["Sharma","Verma","Gupta","Singh","Kumar","Patel","Shah","Jain",
             "Agarwal","Mishra","Rao","Reddy","Nair","Iyer","Das","Bose"]

CHAINS = ["Domino's","Biryani Blues","Saravana Bhavan","Faasos",
          "Haldiram's","Bikanervala","Paradise","Behrouz"]
INDIES = ["Spice Route","The Tandoor","Urban Tadka","Sagar Ratna",
          "Moti Mahal","Bawarchi","Cafe Mocha","The Yellow Chilli"]

ITEM_PREFIXES = ["Special","Spicy","Classic","Premium","Chef's","Signature","House"]

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — GENERATE USERS
# ══════════════════════════════════════════════════════════════════════════════

def generate_users(n=1000):
    city_names = [c[0] for c in CITY_CONFIG]
    city_tiers = {c[0]: c[1] for c in CITY_CONFIG}
    city_veg   = {c[0]: c[2] for c in CITY_CONFIG}
    city_pin   = {c[0]: c[3] for c in CITY_CONFIG}

    # 60% Tier1, 40% Tier2 — weight by city slot
    city_weights = [0.14, 0.14, 0.13, 0.10, 0.09,   # Tier1
                    0.08, 0.08, 0.08, 0.08, 0.08]    # Tier2

    rows = []
    for i in range(1, n + 1):
        uid  = f"U{i:04d}"
        city = np.random.choice(city_names, p=city_weights)

        gender = np.random.choice(["M", "F", "Other"], p=[0.52, 0.44, 0.04])
        if gender == "M":
            name = f"{random.choice(FIRST_M)} {random.choice(LAST)}"
        elif gender == "F":
            name = f"{random.choice(FIRST_F)} {random.choice(LAST)}"
        else:
            name = f"{random.choice(FIRST_M + FIRST_F)} {random.choice(LAST)}"

        age_group = np.random.choice(["18-24","25-34","35-44","45+"],
                                     p=[0.35, 0.40, 0.18, 0.07])
        is_veg    = np.random.rand() < city_veg[city]

        # Segment → AOV
        seg = np.random.choice(["budget","mid","premium"], p=[0.40, 0.40, 0.20])
        aov_base = {"budget": (150, 280), "mid": (280, 480), "premium": (480, 850)}[seg]
        aov      = round(np.random.uniform(*aov_base) * np.random.uniform(0.85, 1.15), 2)
        price_s  = {"budget": (0.65, 0.90), "mid": (0.40, 0.70), "premium": (0.10, 0.40)}[seg]
        price_sensitivity = round(np.random.uniform(*price_s), 2)

        # Cuisine preference (city‐biased)
        if city in ("Bangalore", "Kochi"):
            cw = [0.40, 0.10, 0.10, 0.10, 0.05, 0.05, 0.20]
        elif city in ("Delhi", "Lucknow"):
            cw = [0.05, 0.30, 0.15, 0.10, 0.05, 0.25, 0.10]
        elif city == "Mumbai":
            cw = [0.10, 0.20, 0.30, 0.15, 0.15, 0.05, 0.05]
        elif city in ("Hyderabad",):
            cw = [0.10, 0.10, 0.05, 0.10, 0.05, 0.10, 0.50]
        else:
            cw = [1/7] * 7
        n_pref = random.randint(1, 2)
        pref_cuisines = np.random.choice(CUISINES, size=n_pref, replace=False, p=cw).tolist()

        meal_time = np.random.choice(
            ["breakfast","lunch","dinner","evening_snack","late_night"],
            p=[0.10, 0.30, 0.40, 0.12, 0.08]
        )

        # Affinities
        base_dessert = {"Surat": 0.75, "Jaipur": 0.70, "Bangalore": 0.45}.get(city, 0.55)
        dessert_aff  = float(np.clip(np.random.normal(base_dessert, 0.15), 0, 1))
        bev_aff      = round(np.random.uniform(0.2, 0.8), 2)

        acc_age      = random.randint(30, 1825)
        freq_mult    = {"premium": 1.5, "mid": 1.0, "budget": 0.7}[seg]
        total_orders = max(5, min(400, int(acc_age / random.uniform(5, 15) * freq_mult)))

        pin = f"{city_pin[city]}{random.randint(100, 999)}"

        rows.append({
            "user_id": uid, "name": name, "city": city,
            "city_tier": city_tiers[city], "pincode": pin,
            "age_group": age_group, "gender": gender, "is_veg": is_veg,
            "user_segment": seg, "historical_aov": aov,
            "preferred_cuisine": "|".join(pref_cuisines),
            "preferred_meal_time": meal_time,
            "dessert_affinity": round(dessert_aff, 2),
            "beverage_affinity": round(bev_aff, 2),
            "price_sensitivity": price_sensitivity,
            "account_age_days": acc_age,
            "total_orders_lifetime": total_orders,
        })

    return pd.DataFrame(rows)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — GENERATE RESTAURANTS + MENU ITEMS
# ══════════════════════════════════════════════════════════════════════════════

def generate_catalog(n_restaurants=500):
    tier1_cities = ["Mumbai","Delhi","Bangalore","Hyderabad","Pune"]
    tier2_cities = ["Surat","Jaipur","Lucknow","Chandigarh","Kochi"]

    restaurants = []
    menu_items  = []
    itm_counter = 1

    for r_idx in range(1, n_restaurants + 1):
        rid = f"R{r_idx:04d}"

        # City & tier
        tier = np.random.choice(["Tier1", "Tier2"], p=[0.60, 0.40])
        city = random.choice(tier1_cities if tier == "Tier1" else tier2_cities)

        # Name
        is_chain = np.random.rand() < 0.20
        if is_chain:
            rname = f"{random.choice(CHAINS)} {random.choice(['Express','Cloud','Dine-in',''])}"
        else:
            rname = f"{random.choice(INDIES)} {random.choice(['Restaurant','Cafe','Kitchen','Diner',''])}"
        rname = rname.strip()

        c1 = random.choice(CUISINES)
        c2 = random.choice(CUISINES + [None, None])
        if c1 == c2:
            c2 = None

        pr_range = np.random.choice(["budget","mid","premium"], p=[0.50, 0.35, 0.15])

        restaurants.append({
            "restaurant_id": rid, "name": rname, "city": city, "city_tier": tier,
            "cuisine_primary": c1, "cuisine_secondary": c2,
            "price_range": pr_range,
            "avg_rating": round(np.random.uniform(3.2, 4.8), 1),
            "total_orders_lifetime": random.randint(50, 50_000),
            "is_chain": is_chain, "delivery_only": np.random.rand() < 0.40,
            "peak_hours": "12-14,19-22",
        })

        # Build menu from ontology
        valid = ONT_DF[
            (ONT_DF["cuisine"] == c1) |
            (ONT_DF["cuisine"] == c2) |
            (ONT_DF["cuisine"].isin(["Beverage", "Dessert"]))
        ].copy()

        if len(valid) < 12:
            extra = ONT_DF[~ONT_DF["global_item_id"].isin(valid["global_item_id"])].sample(
                min(10, len(ONT_DF) - len(valid)), random_state=r_idx
            )
            valid = pd.concat([valid, extra]).drop_duplicates("global_item_id")

        menu_sz = random.randint(18, 28)
        selected = valid.sample(min(menu_sz, len(valid)), random_state=r_idx)

        bs_idxs = set(random.sample(list(selected.index), min(3, len(selected))))
        pr_mult = {"budget": 1.0, "mid": 1.4, "premium": 2.0}[pr_range]

        for idx, row in selected.iterrows():
            raw_p = np.random.uniform(row["min_p"], row["max_p"]) * pr_mult
            price = int(round(raw_p / 10) * 10) - 1
            is_bs = idx in bs_idxs
            awo   = random.randint(50, 500) if is_bs else random.randint(1, 40)
            prefix = random.choice(ITEM_PREFIXES + [""])
            display_name = f"{prefix} {row['global_item_id'].replace('_',' ').title()}".strip()

            menu_items.append({
                "item_id":        f"ITM{itm_counter:05d}",
                "restaurant_id":  rid,
                "item_name":      display_name,
                "global_item_id": row["global_item_id"],
                "cuisine":        row["cuisine"],
                "category":       row["category"],
                "price":          max(29, price),
                "is_veg":         row["is_veg"],
                "is_bestseller":  is_bs,
                "avg_weekly_orders": awo,
            })
            itm_counter += 1

    return pd.DataFrame(restaurants), pd.DataFrame(menu_items)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — GENERATE ORDER HISTORY
# ══════════════════════════════════════════════════════════════════════════════

def generate_orders(users_df, rests_df, menu_df, n_orders=25000):
    start = datetime(2023, 1, 1)
    end   = datetime(2024, 12, 31)
    days  = (end - start).days

    rest_by_city  = rests_df.groupby("city")["restaurant_id"].apply(list).to_dict()
    menu_by_rest  = {rid: grp.to_dict("records")
                     for rid, grp in menu_df.groupby("restaurant_id")}
    u_list        = users_df.to_dict("records")

    orders, ord_counter = [], 1

    # Assign favorites per user (hash-stable)
    user_favs = {}

    while len(orders) < n_orders:
        u = random.choice(u_list)
        uid = u["user_id"]

        city_rests = rest_by_city.get(u["city"], [])
        if not city_rests:
            continue

        # Favorites (hash-stable per user)
        if uid not in user_favs:
            r_copy = list(city_rests)
            random.Random(uid).shuffle(r_copy)
            user_favs[uid] = r_copy[:4]

        rid = random.choice(user_favs[uid]) if np.random.rand() < 0.60 \
              else random.choice(city_rests)

        r_menu = menu_by_rest.get(rid)
        if not r_menu:
            continue

        # Veg filter
        if u["is_veg"]:
            r_menu = [m for m in r_menu if m["is_veg"]]
        if not r_menu:
            continue

        # Weighted sampling (bestsellers 10×)
        weights = [10 if m["is_bestseller"] else 1 for m in r_menu]
        norm    = sum(weights)
        probs   = [w / norm for w in weights]
        n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.25, 0.38, 0.20, 0.12, 0.05])
        sampled = np.random.choice(r_menu, size=min(n_items, len(r_menu)),
                                   replace=False, p=probs).tolist()
        if not sampled:
            continue

        # Timestamp
        day_off = random.randint(0, days)
        base_dt = start + timedelta(days=day_off)
        hr_lo, hr_hi = MEAL_HOURS[u["preferred_meal_time"]]
        hr = random.randint(hr_lo, hr_hi)
        dt = base_dt.replace(hour=hr, minute=random.randint(0, 59))

        item_ids  = [m["item_id"] for m in sampled]
        total_val = sum(m["price"] for m in sampled)
        pmt = np.random.choice(["UPI","Card","COD","Wallet"], p=[0.55, 0.25, 0.12, 0.08])
        was_late  = np.random.rand() < 0.12
        rating    = None
        if np.random.rand() < 0.70:
            base_r = 5 if not was_late else 2
            rating = max(1, min(5, base_r + random.randint(-1, 1)))

        discount = 0
        if u["user_segment"] == "budget" and np.random.rand() < 0.30:
            discount = random.randint(10, 80)

        orders.append({
            "order_id":          f"ORD{ord_counter:06d}",
            "user_id":           uid,
            "restaurant_id":     rid,
            "city":              u["city"],
            "order_timestamp":   dt.strftime("%Y-%m-%d %H:%M:%S"),
            "items_ordered":     ",".join(item_ids),
            "total_value":       total_val,
            "payment_mode":      pmt,
            "was_late":          was_late,
            "rating_given":      rating,
            "discount_applied":  discount,
        })
        ord_counter += 1

    return pd.DataFrame(orders)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — BUILD USER HISTORY FEATURES FROM ORDERS
# ══════════════════════════════════════════════════════════════════════════════

def build_user_history(orders_df, menu_df):
    """Returns:
    - user_item_count     : {user_id: {item_id: count}}
    - user_cuisine_count  : {user_id: {cuisine: count}}
    - item_cooccur        : {item_id: Counter of co-occurring item_ids}
    """
    menu_lookup = menu_df.set_index("item_id").to_dict("index")

    user_item   = defaultdict(lambda: defaultdict(int))
    user_cuisine= defaultdict(lambda: defaultdict(int))
    cooccur     = defaultdict(lambda: defaultdict(int))

    for _, row in orders_df.iterrows():
        uid   = row["user_id"]
        items = str(row["items_ordered"]).split(",")

        for itm in items:
            itm = itm.strip()
            user_item[uid][itm] += 1
            cuisine = menu_lookup.get(itm, {}).get("cuisine", "Unknown")
            user_cuisine[uid][cuisine] += 1

        # Co-occurrence (unordered pairs)
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                cooccur[a.strip()][b.strip()] += 1
                cooccur[b.strip()][a.strip()] += 1

    return user_item, user_cuisine, cooccur

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 6 — GENERATE CSAO INTERACTIONS (6 NODES)
# ══════════════════════════════════════════════════════════════════════════════

def get_node_for_category(category, use_budget_node=False):
    """Map category to Hexagon node label."""
    return CATEGORY_TO_NODE.get(category, "Node3_CoOccurrence")

def user_item_affinity(uid, item_id, user_item_count, max_count=10):
    """0-1 score: how many times has this user ordered this item before."""
    cnt = user_item_count.get(uid, {}).get(item_id, 0)
    return min(cnt / max_count, 1.0)

def user_cuisine_affinity_score(uid, cuisine, user_cuisine_count):
    """0-1 score: proportion of orders in this cuisine."""
    totals = user_cuisine_count.get(uid, {})
    total  = sum(totals.values()) + 1e-6
    return min(totals.get(cuisine, 0) / total, 1.0)

def generate_csao_interactions(
    users_df, rests_df, menu_df, orders_df,
    user_item_count, user_cuisine_count, cooccur,
    session_sample_rate=0.18,  # ~18% of 25k orders = ~4,500 sessions
):
    u_map   = users_df.set_index("user_id").to_dict("index")
    menu_by_rest = {rid: grp.to_dict("records")
                    for rid, grp in menu_df.groupby("restaurant_id")}
    menu_by_id   = {row["item_id"]: row for row in menu_df.to_dict("records")}

    # Pre-compute per-restaurant max weekly orders for normalisation
    rest_max_awo = menu_df.groupby("restaurant_id")["avg_weekly_orders"].max().to_dict()

    interactions = []
    int_counter  = 1

    sampled_orders = orders_df.sample(frac=session_sample_rate, random_state=42)

    for _, order in sampled_orders.iterrows():
        oid = order["order_id"]
        uid = order["user_id"]
        rid = order["restaurant_id"]
        u   = u_map.get(uid)
        if not u:
            continue

        r_menu = menu_by_rest.get(rid, [])
        if not r_menu:
            continue

        # Veg filter on candidate pool too
        if u["is_veg"]:
            r_menu = [m for m in r_menu if m["is_veg"]]
        if not r_menu:
            continue

        items_ordered = [x.strip() for x in str(order["items_ordered"]).split(",")]
        if len(items_ordered) < 1:
            continue

        # Cart = 1-2 items; future_adds = the rest
        cart_sz     = max(1, min(2, len(items_ordered) - 1))
        cart_items  = items_ordered[:cart_sz]
        future_adds = items_ordered[cart_sz:]

        cart_val  = sum(menu_by_id[i]["price"] for i in cart_items if i in menu_by_id)
        if cart_val <= 0:
            continue

        cart_menu = [menu_by_id[i] for i in cart_items if i in menu_by_id]
        if not cart_menu:
            continue

        anchor = cart_menu[0]
        anchor_cuisine = anchor.get("cuisine", "Unknown")

        # Embedding variance proxy: how many distinct categories in cart
        cart_categories = [menu_by_id[i]["category"] for i in cart_items if i in menu_by_id]
        n_unique_cats   = len(set(cart_categories))
        emb_var         = round(min((n_unique_cats - 1) * 0.3 + np.random.uniform(0, 0.2), 1.0), 2)
        is_chaos        = 1 if emb_var >= 0.5 else 0

        max_awo = rest_max_awo.get(rid, 1) or 1

        # ── Build candidate list ───────────────────────────────────────────
        candidates_shown = []  # list of (item_dict, node_label, was_added)
        used_ids = set(cart_items)

        # 1. POSITIVE CANDIDATES — ground truth future adds (nodes by category)
        for fa_id in future_adds:
            if fa_id not in menu_by_id:
                continue
            fa = menu_by_id[fa_id]
            if fa_id in used_ids:
                continue
            node = CATEGORY_TO_NODE.get(fa["category"], "Node3_CoOccurrence")
            candidates_shown.append((fa, node, 1))
            used_ids.add(fa_id)

        pool = [m for m in r_menu if m["item_id"] not in used_ids]
        random.shuffle(pool)

        # 2. NODE1_Extension — same-cuisine Extension items not in order
        node1_pool = [m for m in pool if m["category"] == "Extension"
                      and m["cuisine"] == anchor_cuisine
                      and m["item_id"] not in used_ids][:2]
        for m in node1_pool:
            wa = 1 if np.random.rand() < NODE_ACCEPT_PROB["Node1_Extension"] else 0
            candidates_shown.append((m, "Node1_Extension", wa))
            used_ids.add(m["item_id"])

        # 2b. NODE2_Texture — same-cuisine Side items (sensory contrast)
        node2_pool = [m for m in pool if m["category"] == "Side"
                      and m["cuisine"] == anchor_cuisine
                      and m["item_id"] not in used_ids][:2]
        for m in node2_pool:
            wa = 1 if np.random.rand() < NODE_ACCEPT_PROB["Node2_Texture"] else 0
            candidates_shown.append((m, "Node2_Texture", wa))
            used_ids.add(m["item_id"])

        # 3. NODE3_CoOccurrence — co-occurring items with cart
        cooc_scores = defaultdict(int)
        for ci in cart_items:
            for co_id, cnt in cooccur.get(ci, {}).items():
                if co_id not in used_ids:
                    cooc_scores[co_id] += cnt
        top_cooc = sorted(cooc_scores, key=cooc_scores.get, reverse=True)[:2]
        for co_id in top_cooc:
            if co_id not in menu_by_id or co_id in used_ids:
                continue
            co_item = menu_by_id[co_id]
            # Hard constraint: must be from same restaurant AND respect veg preference
            if co_item["restaurant_id"] != rid:
                continue
            if u["is_veg"] and not co_item["is_veg"]:
                continue
            wa = 1 if np.random.rand() < NODE_ACCEPT_PROB["Node3_CoOccurrence"] else 0
            candidates_shown.append((co_item, "Node3_CoOccurrence", wa))
            used_ids.add(co_id)

        # 4. NODE4_Beverage — geo-temporal beverage (weighted by user bev affinity)
        bev_pool = [m for m in pool if m["category"] == "Beverage"
                    and m["item_id"] not in used_ids]
        if bev_pool:
            bev_pick = random.choice(bev_pool)
            bev_accept_p = NODE_ACCEPT_PROB["Node4_Beverage"] * (0.6 + 0.8 * u["beverage_affinity"])
            wa = 1 if np.random.rand() < bev_accept_p else 0
            candidates_shown.append((bev_pick, "Node4_Beverage", wa))
            used_ids.add(bev_pick["item_id"])

        # 5. NODE5_Dessert — regional dessert (weighted by user dessert affinity)
        des_pool = [m for m in pool if m["category"] == "Dessert"
                    and m["item_id"] not in used_ids]
        if des_pool:
            des_pick = random.choice(des_pool)
            des_accept_p = NODE_ACCEPT_PROB["Node5_Dessert"] * (0.5 + u["dessert_affinity"])
            wa = 1 if np.random.rand() < des_accept_p else 0
            candidates_shown.append((des_pick, "Node5_Dessert", wa))
            used_ids.add(des_pick["item_id"])

        # 6. NODE6_BudgetHabit — same-cuisine items within AOV headroom
        aov_headroom = u["historical_aov"] - cart_val
        budget_pool  = [m for m in pool
                        if m["price"] <= max(aov_headroom, 50)
                        and m["item_id"] not in used_ids
                        and m["category"] not in ("Beverage", "Dessert")
                        and m["cuisine"] == anchor_cuisine]
        if budget_pool:
            budget_pick = random.choice(budget_pool)
            wa = 1 if np.random.rand() < NODE_ACCEPT_PROB["Node6_BudgetHabit"] else 0
            candidates_shown.append((budget_pick, "Node6_BudgetHabit", wa))
            used_ids.add(budget_pick["item_id"])

        # 7. NOISE — same-cuisine hard negatives (NOT random whole-menu)
        # Rebuild pool after prior node additions updated used_ids
        remaining_pool = [m for m in r_menu if m["item_id"] not in used_ids]
        noise_same  = [m for m in remaining_pool if m["cuisine"] == anchor_cuisine]
        noise_other = [m for m in remaining_pool if m["cuisine"] != anchor_cuisine]
        # Prefer same-cuisine (harder negatives), pad with any
        noise_candidates = noise_same + noise_other
        # Deduplicate by item_id preserving order
        seen_noise = set()
        noise_dedup = []
        for m in noise_candidates:
            if m["item_id"] not in seen_noise:
                seen_noise.add(m["item_id"])
                noise_dedup.append(m)
        random.shuffle(noise_dedup)
        n_noise = random.randint(1, 2)
        for nm in noise_dedup[:n_noise]:
            # ~12% acceptance for noise (impulse buy simulation)
            wa = 1 if np.random.rand() < NODE_ACCEPT_PROB["Noise"] else 0
            candidates_shown.append((nm, "Noise", wa))
            used_ids.add(nm["item_id"])

        # Skip sessions with no candidates
        if not candidates_shown:
            continue

        # ── Write interaction rows ─────────────────────────────────────────
        for (cand, node, was_added) in candidates_shown:
            cand_id = cand["item_id"]

            # User-item affinity: historical order count for this specific item
            u_item_aff = user_item_affinity(uid, cand_id, user_item_count)
            u_cuis_aff = user_cuisine_affinity_score(uid, cand.get("cuisine",""), user_cuisine_count)
            # Add realistic noise to break circular popularity→label correlation.
            # Without noise, popularity perfectly predicts was_added because
            # popular items dominate orders — making the baseline too strong.
            raw_pop    = cand["avg_weekly_orders"] / max_awo
            pop_score  = float(np.clip(raw_pop + np.random.normal(0, 0.15), 0.0, 1.0))
            pop_score  = round(pop_score, 3)

            interactions.append({
                "interaction_id":        f"INT{int_counter:06d}",
                "session_id":            oid,
                "user_id":               uid,
                "restaurant_id":         rid,
                "interaction_timestamp": order["order_timestamp"],
                "city":                  u["city"],
                "city_tier":             u["city_tier"],
                "user_segment":          u["user_segment"],
                "user_historical_aov":   u["historical_aov"],
                "hour_of_day":           int(order["order_timestamp"][11:13]),
                "day_of_week":           pd.Timestamp(order["order_timestamp"]).dayofweek,
                "meal_time":             u["preferred_meal_time"],
                "cart_items":            ",".join(cart_items),
                "cart_value":            cart_val,
                "n_items_in_cart":       len(cart_items),
                "anchor_cuisine":        anchor_cuisine,
                "embedding_variance":    emb_var,
                "is_chaos_cart":         is_chaos,
                "primary_cart_item":     anchor["item_id"],
                "candidate_item_id":     cand_id,
                "candidate_item_name":   cand["item_name"],
                "candidate_global_id":   cand["global_item_id"],
                "candidate_category":    cand["category"],
                "candidate_cuisine":     cand.get("cuisine", ""),
                "candidate_price":       cand["price"],
                "candidate_is_veg":      cand["is_veg"],
                "price_ratio":           round(cand["price"] / max(cart_val, 1), 3),
                "aov_headroom":          round(u["historical_aov"] - cart_val, 2),
                "hexagon_node":          node,
                "user_item_affinity":    round(u_item_aff, 3),
                "user_cuisine_affinity": round(u_cuis_aff, 3),
                "item_popularity_score": pop_score,
                "was_added":             was_added,
            })
            int_counter += 1

    return pd.DataFrame(interactions)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 7 — VALIDATION & SAVE
# ══════════════════════════════════════════════════════════════════════════════

def validate_and_save(users_df, rests_df, menu_df, orders_df, csao_df):
    print("\n" + "="*55)
    print("  VALIDATION CHECKS")
    print("="*55)

    menu_prices = menu_df.set_index("item_id")["price"].to_dict()
    veg_users   = set(users_df[users_df["is_veg"]]["user_id"])
    veg_items   = set(menu_df[menu_df["is_veg"]]["item_id"])
    u_city      = dict(zip(users_df["user_id"], users_df["city"]))
    r_city      = dict(zip(rests_df["restaurant_id"], rests_df["city"]))

    # FK checks
    assert orders_df["user_id"].isin(users_df["user_id"]).all(), "FK fail: order→user"
    assert orders_df["restaurant_id"].isin(rests_df["restaurant_id"]).all(), "FK fail: order→rest"
    print("[OK] FK integrity: PASS")

    # Math check (sample 500)
    math_errs = 0
    for _, row in orders_df.sample(min(500, len(orders_df)), random_state=1).iterrows():
        items = str(row["items_ordered"]).split(",")
        calc  = sum(menu_prices.get(i.strip(), 0) for i in items)
        if abs(calc - row["total_value"]) > 1:
            math_errs += 1
    assert math_errs == 0, f"Math mismatch in {math_errs} orders"
    print("[OK] Total value math: PASS")

    # Veg constraint
    veg_viols = 0
    for _, row in orders_df.iterrows():
        if row["user_id"] in veg_users:
            for i in str(row["items_ordered"]).split(","):
                if i.strip() not in veg_items:
                    veg_viols += 1
    assert veg_viols == 0, f"Veg violations: {veg_viols}"
    print(f"[OK] Veg constraint violations: 0")

    # City constraint
    city_viols = 0
    for _, row in orders_df.iterrows():
        if u_city.get(row["user_id"]) != r_city.get(row["restaurant_id"]):
            city_viols += 1
    assert city_viols == 0, f"City violations: {city_viols}"
    print(f"[OK] City constraint violations: 0")

    # CSAO label stats
    acc = csao_df["was_added"].mean()
    print(f"\n[STATS] CSAO acceptance rate: {acc:.2%}")
    print("\nAcceptance by Hexagon Node:")
    node_acc = csao_df.groupby("hexagon_node")["was_added"].mean().sort_values(ascending=False)
    for node, rate in node_acc.items():
        print(f"  {node:<22} {rate:.3f}")

    print("\nSaving CSV files...")
    users_df.to_csv("users.csv", index=False)
    rests_df.to_csv("restaurants.csv", index=False)
    menu_df.to_csv("menu_items.csv", index=False)
    orders_df.to_csv("order_history.csv", index=False)
    csao_df.to_csv("csao_interactions.csv", index=False)

    print("\n" + "="*55)
    print("  DATASET SUMMARY")
    print("="*55)
    print(f"  Users:               {len(users_df):,}")
    print(f"  Restaurants:         {len(rests_df):,}")
    print(f"  Menu Items:          {len(menu_df):,}")
    print(f"  Orders:              {len(orders_df):,}")
    print(f"  CSAO Interactions:   {len(csao_df):,}")
    print(f"  Target acceptance:   40-46%  |  Actual: {acc:.2%}")
    print("="*55)
    print("[OK] All files saved successfully!\n")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Phase 1/5 — Generating users...")
    users_df = generate_users(1000)

    print("Phase 2/5 — Generating restaurants & menus...")
    rests_df, menu_df = generate_catalog(500)

    print("Phase 3/5 — Generating order history (25,000 orders)...")
    orders_df = generate_orders(users_df, rests_df, menu_df, n_orders=25000)

    print("Phase 4/5 — Building user history & co-occurrence matrix...")
    user_item_count, user_cuisine_count, cooccur = build_user_history(orders_df, menu_df)

    print("Phase 5/5 — Generating CSAO interactions (6 Hexagon nodes)...")
    csao_df = generate_csao_interactions(
        users_df, rests_df, menu_df, orders_df,
        user_item_count, user_cuisine_count, cooccur,
        session_sample_rate=0.18,
    )

    validate_and_save(users_df, rests_df, menu_df, orders_df, csao_df)
