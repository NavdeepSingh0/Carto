import requests, json

restaurants = requests.get("http://localhost:8085/api/restaurants").json()

r = restaurants[0]
menu = requests.get(f"http://localhost:8085/api/menu/{r['restaurant_id']}").json()

with open("test_output.txt", "w", encoding="utf-8") as f:
    f.write(f"Restaurant: {r['name']} ({r['restaurant_id']})\n")
    f.write(f"Menu items: {len(menu)}\n\n")
    
    cats = {}
    for m in menu:
        c = m.get("category", "MISSING")
        cats.setdefault(c, []).append(m["item_name"])
    
    for cat, items in cats.items():
        f.write(f"  {cat}: {items}\n")
    
    # Test with a Main item
    mains = [m for m in menu if m.get("category") == "Main"]
    desserts = [m for m in menu if m.get("category") == "Dessert"]
    beverages = [m for m in menu if m.get("category") == "Beverage"]
    
    # Test 1: Single main
    cart_item = mains[0] if mains else menu[0]
    f.write(f"\n{'='*70}\n")
    f.write(f"TEST 1: Cart = [{cart_item['item_name']}] (cat={cart_item.get('category')})\n")
    f.write(f"{'='*70}\n")
    
    rec = requests.post("http://localhost:8085/api/recommend", json={
        "restaurant_id": r["restaurant_id"],
        "cart_item_ids": [cart_item["item_id"]],
        "profile": {"segment": "mid", "is_veg": False, "city": "Mumbai", "meal_time": "dinner"}
    }).json()
    
    for x in rec.get("recommendations", []):
        f.write(f"  {x['item_name']:30} cat={x.get('category','?'):12} node={x.get('hexagon_node','?'):22} score={x.get('score',0):.4f} cuisine={x.get('cuisine','?')}\n")
    f.write(f"  AOV={rec.get('user_aov')}, CartVal={rec.get('cart_value')}, Headroom={rec.get('headroom')}\n")

    # Test 2: Dessert only (the "Kulfi" scenario)
    if desserts:
        cart_item2 = desserts[0]
        f.write(f"\n{'='*70}\n")
        f.write(f"TEST 2 (Dessert only): Cart = [{cart_item2['item_name']}] (cat={cart_item2.get('category')})\n")
        f.write(f"{'='*70}\n")
        
        rec2 = requests.post("http://localhost:8085/api/recommend", json={
            "restaurant_id": r["restaurant_id"],
            "cart_item_ids": [cart_item2["item_id"]],
            "profile": {"segment": "mid", "is_veg": False, "city": "Mumbai", "meal_time": "dinner"}
        }).json()
        
        for x in rec2.get("recommendations", []):
            f.write(f"  {x['item_name']:30} cat={x.get('category','?'):12} node={x.get('hexagon_node','?'):22} score={x.get('score',0):.4f} cuisine={x.get('cuisine','?')}\n")
    
    # Test 3: Main + Dessert combo
    if mains and desserts:
        f.write(f"\n{'='*70}\n")
        f.write(f"TEST 3: Cart = [{mains[0]['item_name']}, {desserts[0]['item_name']}]\n")
        f.write(f"{'='*70}\n")
        
        rec3 = requests.post("http://localhost:8085/api/recommend", json={
            "restaurant_id": r["restaurant_id"],
            "cart_item_ids": [mains[0]["item_id"], desserts[0]["item_id"]],
            "profile": {"segment": "mid", "is_veg": False, "city": "Mumbai", "meal_time": "dinner"}
        }).json()
        
        for x in rec3.get("recommendations", []):
            f.write(f"  {x['item_name']:30} cat={x.get('category','?'):12} node={x.get('hexagon_node','?'):22} score={x.get('score',0):.4f} cuisine={x.get('cuisine','?')}\n")

print("Output written to test_output.txt")
