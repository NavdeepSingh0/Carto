import pandas as pd

print("Loading datasets...")
orders  = pd.read_csv("order_history.csv")
csao    = pd.read_csv("csao_interactions.csv")

print("Building lookup table from items_ordered...")
# Build lookup: session_id → set of item_ids ordered
order_items = orders.set_index('order_id')['items_ordered'].apply(
    lambda x: set(str(x).split(','))
).to_dict()

# Rederive was_added from ground truth
def derive_label(row):
    items_in_order = order_items.get(row['session_id'], set())
    return 1 if str(row['candidate_item_id']).strip() in items_in_order else 0

print("Applying label fix...")
csao['was_added'] = csao.apply(derive_label, axis=1)

print("\n--- RESULTS ---")
print(f"New acceptance rate: {csao['was_added'].mean():.2%}")
print(f"was_added=1: {csao['was_added'].sum():,}")
print("\nAcceptance by Hexagon Node:")
print(csao.groupby('hexagon_node')['was_added'].mean().sort_values(ascending=False).round(3))

print("\nSaving csao_interactions_fixed.csv...")
def save_csv(df, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"=== FILE: {filename} ===\n")
        df.to_csv(f, index=False, lineterminator='\n')

save_csv(csao, "csao_interactions_fixed.csv")
print("Done!")
