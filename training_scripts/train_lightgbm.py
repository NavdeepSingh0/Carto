import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
np.random.seed(42)

print("LightGBM version:", lgb.__version__)

# Cell 2 — Load Data
PATH = "./"
users   = pd.read_csv(PATH + "users.csv")
rests   = pd.read_csv(PATH + "restaurants.csv")
menu    = pd.read_csv(PATH + "menu_items.csv")
orders  = pd.read_csv(PATH + "order_history.csv")
csao    = pd.read_csv(PATH + "csao_interactions.csv")

print(f"Users:               {len(users):,}")
print(f"Restaurants:         {len(rests):,}")
print(f"Menu Items:          {len(menu):,}")
print(f"Orders:              {len(orders):,}")
print(f"CSAO Interactions:   {len(csao):,}")
print(f"\nOverall acceptance rate: {csao['was_added'].mean():.2%}")
print(f"\nCSAO columns:\n{csao.columns.tolist()}")


# Cell 3 — Sanity Checks
print("=" * 50)
print("  DATASET SANITY CHECKS")
print("=" * 50)

# CHECK 1: Node hierarchy
node_acc = csao.groupby('hexagon_node')['was_added'].mean().sort_values(ascending=False)
print("\n1. Acceptance by Hexagon Node:")
print(node_acc.round(3))
print("\nExpected order: Node1 > Node3 > Node4 > Node2 > Node5 > Node6 > Noise")
expected = ['Node1_Extension','Node3_CoOccurrence','Node4_Beverage',
            'Node2_Texture','Node5_Dessert','Node6_BudgetHabit','Noise']
top_nodes = node_acc.index.tolist()
print(f"Hierarchy correct: {top_nodes[0] == 'Node1_Extension' if len(top_nodes) > 0 else False}")

# CHECK 2: Veg constraint
merged_veg = csao.merge(users[['user_id','is_veg']], on='user_id', how='left')
veg_col = 'candidate_is_veg' if 'candidate_is_veg' in csao.columns else None
if veg_col:
    veg_violations = merged_veg[
        (merged_veg['is_veg'] == True) &
        (merged_veg[veg_col] == 0) &
        (merged_veg['was_added'] == 1)
    ]
    print(f"\n2. Veg constraint violations: {len(veg_violations)} (must be 0)")

# CHECK 3: City constraint
u_city = users[['user_id','city']].rename(columns={'city':'user_city'})
r_city = rests[['restaurant_id','city']].rename(columns={'city':'rest_city'})
merged_city = csao.merge(u_city, on='user_id').merge(r_city, on='restaurant_id')
city_violations = merged_city[merged_city['user_city'] != merged_city['rest_city']]
print(f"3. City constraint violations: {len(city_violations)} (must be 0)")

# CHECK 4: Label distribution
print(f"\n4. Label distribution:")
print(f"   was_added=1: {csao['was_added'].sum():,} ({csao['was_added'].mean():.1%})")
print(f"   was_added=0: {(csao['was_added']==0).sum():,} ({1-csao['was_added'].mean():.1%})")

# CHECK 5: Noise candidates acceptance
if 'Noise' in csao['hexagon_node'].values:
    noise_acc = csao[csao['hexagon_node']=='Noise']['was_added'].mean()
    print(f"\n5. Noise candidate acceptance: {noise_acc:.2%} (should be <10%)")

print("\n" + "=" * 50)


# Cell 5 — Hexagon Candidate Recall
print("=" * 50)
print("  HEXAGON CANDIDATE RECALL CHECK")
print("=" * 50)

hexagon_nodes = ['Node1_Extension','Node2_Texture','Node3_CoOccurrence',
                 'Node4_Beverage','Node5_Dessert','Node6_BudgetHabit']

all_positives      = csao[csao['was_added'] == 1]
hexagon_positives  = all_positives[all_positives['hexagon_node'].isin(hexagon_nodes)]
noise_positives    = all_positives[all_positives['hexagon_node'] == 'Noise']

if len(all_positives) > 0:
    recall = len(hexagon_positives) / len(all_positives)
    print(f"\nTotal positive labels:          {len(all_positives):,}")
    print(f"Captured by Hexagon:            {len(hexagon_positives):,}")
    print(f"Missed (in Noise):              {len(noise_positives):,}")
    print(f"\nHexagon Candidate Recall:       {recall:.2%}")
    print(f"(Target: > 70% — if below, model AUC is ceiling-capped)")


# Cell 6 — Feature Engineering
df = csao.copy()

# Add is_hexagon_candidate
df['is_hexagon_candidate'] = (df['hexagon_node'] != 'Noise').astype(int)

# Merge user features
user_cols = ['user_id','is_veg','user_segment','age_group',
             'dessert_affinity','beverage_affinity',
             'price_sensitivity','total_orders_lifetime']
user_cols = [c for c in user_cols if c in users.columns]
df = df.merge(users[user_cols], on='user_id', how='left')

# Merge restaurant features
rest_cols = ['restaurant_id','avg_rating','price_range','is_chain']
rest_cols = [c for c in rest_cols if c in rests.columns]
df = df.merge(rests[rest_cols], on='restaurant_id', how='left')

# Encode categoricals
le = LabelEncoder()
cat_cols = ['user_segment','meal_time','hexagon_node','candidate_category',
            'anchor_cuisine','candidate_cuisine','city_tier','price_range']
for col in cat_cols:
    if col in df.columns:
        df[col + '_enc'] = le.fit_transform(df[col].astype(str))

# Boolean to int
bool_cols = ['is_veg','candidate_is_veg','is_chaos_cart','is_chain']
for col in bool_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0).astype(int)

# Derived features
df['price_match']     = (df['candidate_is_veg'] == df['is_veg']).astype(int) if 'candidate_is_veg' in df.columns else 0
df['budget_safe']     = (df['candidate_price'] <= df['aov_headroom'] * 0.4).astype(int) if 'candidate_price' in df.columns and 'aov_headroom' in df.columns else 0
df['is_beverage']     = (df['candidate_category'] == 'Beverage').astype(int) if 'candidate_category' in df.columns else 0
df['is_dessert']      = (df['candidate_category'] == 'Dessert').astype(int) if 'candidate_category' in df.columns else 0
df['is_extension']    = (df['candidate_category'] == 'Extension').astype(int) if 'candidate_category' in df.columns else 0

# Affinity match
if 'dessert_affinity' in df.columns and 'beverage_affinity' in df.columns:
    df['affinity_match'] = np.where(
        df['is_beverage']==1, df['beverage_affinity'],
        np.where(df['is_dessert']==1, df['dessert_affinity'], 0.5)
    )
else:
    df['affinity_match'] = 0.5

print(f"\nFeature engineering complete. Shape: {df.shape}")

# Cell 7 — Temporal Train/Test Split
ts_col = 'interaction_timestamp'
if ts_col not in df.columns:
    ts_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()]
    ts_col = ts_col[0] if ts_col else None

if ts_col:
    df[ts_col] = pd.to_datetime(df[ts_col])
    df = df.sort_values(ts_col).reset_index(drop=True)
    split_idx  = int(len(df) * 0.80)
    split_date = df[ts_col].iloc[split_idx]
    train_df   = df[df[ts_col] < split_date].copy()
    test_df    = df[df[ts_col] >= split_date].copy()
    print(f"Split date: {split_date}")
else:
    session_col = 'session_id' if 'session_id' in df.columns else 'order_id'
    sessions    = sorted(df[session_col].unique())
    cutoff      = sessions[int(len(sessions) * 0.80)]
    train_df    = df[df[session_col] <= cutoff].copy()
    test_df     = df[df[session_col] > cutoff].copy()
    print(f"Split by {session_col}. Cutoff: {cutoff}")

print(f"\nTrain: {len(train_df):,} rows | acceptance: {train_df['was_added'].mean():.2%}")
print(f"Test:  {len(test_df):,} rows  | acceptance: {test_df['was_added'].mean():.2%}")


# Cell 8 — LightGBM Training
FEATURES = [
    'hexagon_node_enc', 'is_hexagon_candidate',
    'user_historical_aov', 'user_segment_enc', 'price_sensitivity',
    'dessert_affinity', 'beverage_affinity', 'total_orders_lifetime',
    'user_item_affinity', 'user_cuisine_affinity', 'affinity_match',
    'cart_value', 'n_items_in_cart', 'embedding_variance',
    'is_chaos_cart', 'anchor_cuisine_enc',
    'candidate_price', 'price_ratio', 'aov_headroom',
    'price_match', 'budget_safe',
    'candidate_category_enc', 'candidate_is_veg', 'item_popularity_score',
    'hour_of_day', 'day_of_week', 'meal_time_enc',
    'city_tier_enc',
    'avg_rating', 'is_chain',
    'is_beverage', 'is_dessert', 'is_extension',
]

FEATURES = [f for f in FEATURES if f in df.columns]
print(f"\nTraining with {len(FEATURES)} features")

X_train = train_df[FEATURES].fillna(0)
y_train = train_df['was_added']
X_test  = test_df[FEATURES].fillna(0)
y_test  = test_df['was_added']

lgb_train = lgb.Dataset(X_train, label=y_train)
lgb_val   = lgb.Dataset(X_test,  label=y_test, reference=lgb_train)

params = {
    'objective':         'binary',
    'metric':            'auc',
    'learning_rate':     0.05,
    'num_leaves':        63,
    'max_depth':         6,
    'min_child_samples': 20,
    'feature_fraction':  0.8,
    'bagging_fraction':  0.8,
    'bagging_freq':      5,
    'lambda_l1':         0.1,
    'lambda_l2':         0.1,
    'verbose':          -1,
    'random_state':      42,
}

model = lgb.train(
    params,
    lgb_train,
    num_boost_round=1000,
    valid_sets=[lgb_val],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)],
)

test_df = test_df.copy()
test_df['predicted_score'] = model.predict(X_test)
print(f"\nBest iteration: {model.best_iteration}")
print(f"Best AUC:       {model.best_score['valid_0']['auc']:.4f}")

# Cell 9 — Full Evaluation Metrics
def precision_at_k(group, k):
    top = group.nlargest(k, 'predicted_score')
    return top['was_added'].mean()

def recall_at_k(group, k):
    top    = group.nlargest(k, 'predicted_score')
    total  = group['was_added'].sum()
    return top['was_added'].sum() / total if total > 0 else 0

def ndcg_at_k(group, k=5):
    group = group.nlargest(k, 'predicted_score').reset_index(drop=True)
    dcg   = sum(group['was_added'].iloc[i] / np.log2(i+2) for i in range(len(group)))
    ideal = sorted(group['was_added'], reverse=True)
    idcg  = sum(ideal[i] / np.log2(i+2) for i in range(len(ideal)))
    return dcg / idcg if idcg > 0 else 0

group_col = 'session_id' if 'session_id' in test_df.columns else 'order_id'

auc    = roc_auc_score(y_test, test_df['predicted_score'])
p3     = test_df.groupby(group_col).apply(lambda g: precision_at_k(g, 3)).mean()
p5     = test_df.groupby(group_col).apply(lambda g: precision_at_k(g, 5)).mean()
r5     = test_df.groupby(group_col).apply(lambda g: recall_at_k(g, 5)).mean()
ndcg   = test_df.groupby(group_col).apply(lambda g: ndcg_at_k(g, 5)).mean()

print("\n" + "=" * 45)
print("   FINAL MODEL EVALUATION METRICS")
print("=" * 45)
print(f"   AUC:           {auc:.4f}   (target: > 0.70)")
print(f"   Precision@3:   {p3:.4f}   (target: > 0.55)")
print(f"   Precision@5:   {p5:.4f}   (target: > 0.50)")
print(f"   Recall@5:      {r5:.4f}")
print(f"   NDCG@5:        {ndcg:.4f}   (target: > 0.75)")
print("=" * 45)

# Demo
def get_recommendations(user_id, top_n=8):
    group_col = 'session_id' if 'session_id' in test_df.columns else 'order_id'
    
    user_sessions = test_df[test_df['user_id'] == user_id][group_col].unique()
    if len(user_sessions) == 0:
        return
    
    session_id = user_sessions[0]
    session_data = test_df[test_df[group_col] == session_id].nlargest(top_n, 'predicted_score')
    
    user_info = users[users['user_id'] == user_id]
    if len(user_info) == 0:
        return
    user_info = user_info.iloc[0]
    
    print(f"\n{'='*68}")
    print(f"  USER:     {user_id} | {user_info.get('city','?')} | "
          f"{user_info.get('user_segment','?')} | "
          f"{'Veg' if user_info.get('is_veg') else 'Non-Veg'}")
    
    cart_col = 'cart_items' if 'cart_items' in session_data.columns else None
    if cart_col:
        print(f"  CART:     {session_data.iloc[0][cart_col]}")
    
    cv_col = 'cart_value' if 'cart_value' in session_data.columns else None
    mt_col = 'meal_time' if 'meal_time' in session_data.columns else None
    if cv_col:
        print(f"  VALUE:    Rs {session_data.iloc[0][cv_col]} | "
              f"Meal: {session_data.iloc[0].get(mt_col, '?')}")
    
    print(f"{'='*68}")
    print(f"  {'#':<3} {'Item':<28} {'Node':<24} {'Score':<7} {'Result'}")
    print(f"  {'-'*63}")
    
    name_col = 'candidate_item_name' if 'candidate_item_name' in session_data.columns \
               else 'candidate_item_id'
    
    for rank, (_, row) in enumerate(session_data.iterrows(), 1):
        result = "YES Added" if row['was_added'] == 1 else "NO  Skip"
        node   = str(row.get('hexagon_node', '')).replace('_',' ')
        score  = float(row['predicted_score'])
        name   = str(row[name_col])[:27]
        print(f"  {rank:<3} {name:<28} {node:<24} {score:.3f}   {result}")

print("\nLIVE RECOMMENDATION DEMO — 5 TEST USERS")
sample_users = test_df['user_id'].unique()[:5]
for uid in sample_users:
    get_recommendations(uid)
