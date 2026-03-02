# CSAO App — Complete UX Redesign Brief
## For Antigravity / Implementation Agent

---

## THE CORE PROBLEM WITH CURRENT UX

The current app has a **workflow problem**, not just a visual problem. The user has to:
1. Set 5 dropdowns in the sidebar (city, segment, diet, meal time, restaurant)
2. Separately find and add items in a multiselect at the bottom of the sidebar
3. Scroll back up to see the cart
4. Click a button in the main area
5. Scroll down to see results

This is 5 context switches for what should be a fluid 3-step experience. Every interaction feels like filling out a form, not building a cart.

---

## THE TARGET EXPERIENCE (3 Steps, No Forms)

```
STEP 1 → Who are you?        (Profile selection — visual cards, not dropdowns)
STEP 2 → What's in your cart? (Menu browser — add items naturally)
STEP 3 → See recommendations  (Live rail that updates as you add items)
```

The app should feel like using a real food ordering interface, not configuring a data pipeline.

---

## VISUAL DESIGN SYSTEM

### Colors
```python
BG_PRIMARY    = "#1A1A1A"   # Main background — warm dark
BG_CARD       = "#242424"   # Card surfaces
BG_SIDEBAR    = "#161616"   # Sidebar / left panel
ACCENT        = "#F5A623"   # Amber yellow — primary CTA, highlights
ACCENT_SOFT   = "#2A2118"   # Amber tinted dark — selected state backgrounds
TEXT_PRIMARY  = "#F5F5F5"   # Main text
TEXT_MUTED    = "#888888"   # Labels, metadata
BORDER        = "#333333"   # Subtle card borders
SUCCESS       = "#22C55E"   # Veg indicator
DANGER        = "#EF4444"   # Non-veg indicator
```

### Node Badge Colors (one per Hexagon node)
```python
NODE_COLORS = {
    "Node1_Extension":    "#F5A623",  # Amber  — core completion
    "Node2_Texture":      "#A78BFA",  # Purple — sensory contrast
    "Node3_CoOccurrence": "#38BDF8",  # Sky    — collaborative filter
    "Node4_Beverage":     "#34D399",  # Emerald — drinks
    "Node5_Dessert":      "#F472B6",  # Pink   — dessert
    "Node6_BudgetHabit":  "#FB923C",  # Orange — budget optimizer
    "Noise":              "#6B7280",  # Gray   — baseline
}
```

### Typography
```css
/* Inject via st.markdown */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* { font-family: 'Plus Jakarta Sans', sans-serif; }
```

### Global CSS Injections (required)
```css
/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
.stDeployButton { display: none; }

/* Remove default padding */
.block-container { padding-top: 1rem; padding-bottom: 0; }

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #161616;
    border-right: 1px solid #2A2A2A;
}

/* Remove default widget borders */
.stSelectbox > div > div {
    background-color: #242424;
    border: 1px solid #333333;
    border-radius: 8px;
    color: #F5F5F5;
}
```

---

## LAYOUT ARCHITECTURE

### Overall Structure
```
┌─────────────────────────────────────────────────────┐
│  LEFT PANEL (300px fixed)   │  RIGHT PANEL (fluid)  │
│                             │                       │
│  Step 1: Profile Selector   │  Step 3: CSAO Rail    │
│  Step 2: Cart Builder       │  (recommendations)    │
│                             │                       │
│  Live Cart Summary          │  Metric cards         │
│  [Generate Button]          │  Why this? Panel      │
└─────────────────────────────────────────────────────┘
```

The left panel handles ALL input. The right panel shows ALL output. No context switching.

---

## STEP 1 — PROFILE SELECTOR (Replace all dropdowns)

### Current (Bad)
Five separate dropdowns: City, User Segment, Dietary Preference, Meal Time, Restaurant. User has to read each label and make individual selections. Feels like a government form.

### New Design (Visual Card Grid)

**User Segment** — 3 clickable cards, not a dropdown:
```
┌─────────┐  ┌─────────┐  ┌─────────┐
│   🏷️    │  │   ⚖️    │  │   💎    │
│ Budget  │  │   Mid   │  │ Premium │
│ ₹150-   │  │ ₹280-   │  │ ₹480+   │
│  280    │  │  480    │  │         │
└─────────┘  └─────────┘  └─────────┘
```
Selected state: amber border + amber-tinted background. One click, done.

**Dietary Preference** — 2 toggle pills:
```
[ 🟢 Veg ]  [ 🔴 Non-Veg ]
```
Not a dropdown. One click switches between them.

**Meal Time** — Time-aware auto-selection with manual override:
```python
from datetime import datetime
hour = datetime.now().hour
if 6 <= hour < 11:   default = "Breakfast"
elif 11 <= hour < 16: default = "Lunch"
elif 16 <= hour < 19: default = "Evening Snack"
elif 19 <= hour < 23: default = "Dinner"
else:                  default = "Late Night"
```
Show as pill selector but pre-select based on current time. User sees it auto-set and can override. This is a small detail judges will notice.

**City** — Keep as dropdown but style it properly. Not critical enough for card treatment.

**Restaurant** — Move this to Step 2 (it's part of cart building, not profile).

---

## STEP 2 — CART BUILDER (Replace multiselect)

### Current (Bad)
A multiselect widget at the bottom of the sidebar showing truncated item names. No prices, no categories, no cuisine. User is guessing what they're adding.

### New Design — Searchable Menu Browser

**Restaurant selector first** (styled dropdown with cuisine tag):
```
┌─────────────────────────────────┐
│ 🍽️ Saravana Bhavan Cloud...     │
│    South Indian · ⭐ 4.3        │
└─────────────────────────────────┘
```

**Category filter tabs** (horizontal pills, not dropdown):
```
[ All ]  [ Main ]  [ Side ]  [ Beverage ]  [ Dessert ]  [ Extension ]
```
Click a tab → menu filters instantly.

**Menu item cards** (scrollable list, not multiselect):
```
┌──────────────────────────────────────┐
│ 🟢 Masala Dosa              ₹120     │
│    South Indian · Main               │
│                          [ + Add ]   │
└──────────────────────────────────────┘
```
- Green dot = veg, Red dot = non-veg
- Non-veg items auto-hidden when Veg preference selected
- `[ + Add ]` button adds to cart immediately
- Once added, button changes to `[ ✓ Added ]` with green styling

**Implementation:**
```python
# Filter menu items reactively
filtered_menu = menu[
    (menu['restaurant_id'] == selected_restaurant) &
    (menu['category'].isin(selected_categories) if selected_categories else True) &
    (menu['is_veg'] == True if is_veg_user else True)
]

for _, item in filtered_menu.iterrows():
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        dot = "🟢" if item['is_veg'] else "🔴"
        st.markdown(f"{dot} **{item['item_name']}**")
        st.caption(f"{item['candidate_cuisine']} · {item['category']}")
    with col2:
        st.markdown(f"**₹{item['price']}**")
    with col3:
        if item['item_id'] in st.session_state.cart:
            st.markdown("✓ Added")
        else:
            if st.button("+ Add", key=f"add_{item['item_id']}"):
                st.session_state.cart[item['item_id']] = item
                st.rerun()
```

---

## LIVE CART SUMMARY (Bottom of Left Panel)

Always visible. Updates live as items are added. Never requires scrolling.

```
━━━━━━━━━━━━━━━━━━━━━━
YOUR CART  (2 items)
━━━━━━━━━━━━━━━━━━━━━━
🟢 Masala Dosa        ₹120   [×]
🔴 Chicken Biryani    ₹220   [×]
━━━━━━━━━━━━━━━━━━━━━━
Cart Value:    ₹340
Your Avg AOV:  ₹480
Headroom:      ₹140  ← amber colored
━━━━━━━━━━━━━━━━━━━━━━
```

Headroom number changes color:
- Green if headroom > ₹200 (plenty of room for add-ons)
- Amber if ₹50-200
- Red if < ₹50 (near AOV limit)

This is a live signal to the user and to judges watching — the system is budget-aware in real time.

**Generate Button:**
```python
# Disabled until at least 1 item in cart
if len(st.session_state.cart) == 0:
    st.button("Add items to generate recommendations", disabled=True)
else:
    if st.button("⚡ Generate CSAO Rail", use_container_width=True):
        # trigger recommendation pipeline
```

Button is disabled with explanatory text until cart has items. No confusing empty states.

---

## STEP 3 — RECOMMENDATION RAIL (Right Panel)

### Current (Bad)
Results appear as a plain table or list after clicking the button. No visual hierarchy, no explanation of why each item was recommended.

### New Design — Horizontal Scrollable Rail

**Header:**
```
CSAO RAIL  ·  8 recommendations  ·  Generated in 47ms
```
Latency shown for every generation — judges will see sub-100ms and note it.

**Recommendation Cards (horizontal scroll):**
```
┌─────────────────────┐  ┌─────────────────────┐
│  Node1 Extension    │  │  Node4 Beverage      │
│  ───────────────    │  │  ──────────────────  │
│  Extra Salan        │  │  Mango Lassi         │
│                     │  │                      │
│  🟢 Veg  ·  ₹60    │  │  🟢 Veg  ·  ₹80    │
│                     │  │                      │
│  Confidence         │  │  Confidence          │
│  ████████░░  82%    │  │  ██████░░░░  61%    │
│                     │  │                      │
│  [ + Add to Cart ]  │  │  [ + Add to Cart ]  │
└─────────────────────┘  └─────────────────────┘
```

Each card:
- Node badge at top with node-specific color
- Item name bold
- Veg/non-veg dot + price
- Confidence score as visual progress bar (not just a number)
- Add to Cart button — clicking it actually adds to cart and re-triggers recommendation generation

**Card implementation:**
```python
def render_rec_card(rec, node_colors):
    node = rec['hexagon_node']
    color = node_colors.get(node, '#888888')
    node_label = node.replace('Node1_', '').replace('Node2_', '') \
                     .replace('Node3_', '').replace('Node4_', '') \
                     .replace('Node5_', '').replace('Node6_', '')
    confidence = int(rec['predicted_score'] * 100)
    veg_dot = "🟢" if rec['candidate_is_veg'] else "🔴"
    
    st.markdown(f"""
    <div style="
        background: #242424;
        border: 1px solid #333;
        border-top: 3px solid {color};
        border-radius: 12px;
        padding: 16px;
        min-width: 180px;
    ">
        <span style="
            background: {color}22;
            color: {color};
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">{node_label}</span>
        <div style="margin-top: 12px; font-size: 15px; font-weight: 700;
                    color: #F5F5F5;">{rec['candidate_item_name']}</div>
        <div style="margin-top: 4px; font-size: 13px; color: #888;">
            {veg_dot} · ₹{rec['candidate_price']}
        </div>
        <div style="margin-top: 12px;">
            <div style="font-size: 11px; color: #888; margin-bottom: 4px;">
                Confidence: {confidence}%
            </div>
            <div style="background: #333; border-radius: 4px; height: 4px;">
                <div style="background: {color}; width: {confidence}%;
                            height: 4px; border-radius: 4px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

### Horizontal scroll implementation:
```python
# Render cards in columns
n_recs = len(recommendations)
cols = st.columns(min(n_recs, 4))  # max 4 visible, scroll for rest
for i, (_, rec) in enumerate(recommendations.iterrows()):
    with cols[i % 4]:
        render_rec_card(rec, NODE_COLORS)
```

---

## KPI ROW (Top of Right Panel)

Four metric cards, always visible, updates live:

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 🛒           │ │ 📊           │ │ 💰           │ │ ⚡           │
│ ₹340         │ │ ₹480         │ │ ₹140         │ │ 3            │
│ CART VALUE   │ │ USER AOV     │ │ HEADROOM     │ │ ITEMS        │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

Implementation:
```python
def kpi_card(icon, value, label, color="#F5A623"):
    return f"""
    <div style="
        background: #242424;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
    ">
        <div style="font-size: 24px; margin-bottom: 4px;">{icon}</div>
        <div style="font-size: 28px; font-weight: 800; color: {color};">{value}</div>
        <div style="font-size: 11px; color: #888; font-weight: 600;
                    letter-spacing: 1px; margin-top: 4px;">{label}</div>
    </div>
    """
```

---

## "WHY THIS?" EXPLAINABILITY PANEL

Below the rail. Judges love this. One click expands it.

```python
with st.expander("🔍 Why these recommendations? (Hexagon Logic)"):
    for node_name, node_recs in recommendations.groupby('hexagon_node'):
        color = NODE_COLORS.get(node_name, '#888')
        st.markdown(f"""
        <div style="border-left: 3px solid {color}; padding-left: 12px; margin: 8px 0;">
            <strong style="color: {color};">{node_name}</strong><br>
            <span style="color: #888; font-size: 13px;">{NODE_EXPLANATIONS[node_name]}</span><br>
            <span style="color: #F5F5F5; font-size: 13px;">
                Recommended: {', '.join(node_recs['candidate_item_name'].tolist())}
            </span>
        </div>
        """, unsafe_allow_html=True)
```

Node explanations dict:
```python
NODE_EXPLANATIONS = {
    "Node1_Extension":    "Physically completes the dish — items that belong together",
    "Node2_Texture":      "Adds sensory contrast — crispy with soft, cooling with spicy",
    "Node3_CoOccurrence": "Collaborative filter — other users who ordered this also added",
    "Node4_Beverage":     "Context-aware drink — matched to cuisine, city, and meal time",
    "Node5_Dessert":      "Regional dessert — weighted by user's personal dessert history",
    "Node6_BudgetHabit":  "Budget optimizer — fits within AOV headroom, habit-aligned",
}
```

---

## SESSION STATE MANAGEMENT

All state in `st.session_state`. Never loses context on interaction.

```python
# Initialize at top of app
if 'cart' not in st.session_state:
    st.session_state.cart = {}          # item_id → item dict
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'profile' not in st.session_state:
    st.session_state.profile = {
        'segment': 'mid',
        'is_veg': False,
        'city': 'Mumbai',
        'meal_time': auto_detect_meal_time(),
    }
if 'generation_time_ms' not in st.session_state:
    st.session_state.generation_time_ms = None
```

**Critical:** Every `st.button` click that modifies state must call `st.rerun()` after. This ensures the cart summary, KPI cards, and recommendations all update atomically.

---

## EMPTY STATES (Currently Missing Entirely)

### No items in cart:
```
Right panel shows:

    ┌─────────────────────────────────┐
    │                                 │
    │     🛒                          │
    │                                 │
    │   Your cart is empty            │
    │   Add items from the menu       │
    │   to see CSAO recommendations   │
    │                                 │
    └─────────────────────────────────┘
```

### After generation, no strong recommendations:
```
    ⚠️  Weak signal for this cart combination.
    Try adding a main dish first — the Hexagon
    Extension node works best with a clear anchor item.
```

These two empty states alone make the app feel 10x more professional.

---

## MICRO-INTERACTIONS

Small details that add up:

**Item added to cart** → brief green flash on the cart summary section using `st.toast()`:
```python
st.toast(f"✓ {item['item_name']} added to cart", icon="🛒")
```

**Recommendations generated** → show latency:
```python
import time
start = time.time()
recommendations = generate_recommendations(...)
elapsed_ms = int((time.time() - start) * 1000)
st.caption(f"⚡ Generated in {elapsed_ms}ms")
```

**Veg filter active** → non-veg items in menu show as faded/greyed, not hidden entirely. User can see they exist but can't add them. More informative than making them disappear.

---

## WHAT TO REMOVE ENTIRELY

- The spinning loader emoji in the header banner
- The gradient red/orange banner (replace with clean text header)
- Emoji labels on every sidebar section header
- The `[×]` close button styling that looks like a browser tag
- Any `st.write()` calls that dump raw dataframes to the screen
- The "Configure Session" header in the sidebar — just start with the content

---

## DEPLOYMENT CHECKLIST

Before pushing to Streamlit Cloud:

```
[ ] requirements.txt includes: streamlit, pandas, numpy, lightgbm, scikit-learn, gensim
[ ] All CSV files committed to repo OR loaded from st.cache_data with @st.cache_data decorator
[ ] Model loaded with @st.cache_resource (loads once, not on every interaction)
[ ] App tested with cart of 1 item, 3 items, 5 items
[ ] App tested with Veg user — confirm zero non-veg recommendations
[ ] App tested on mobile viewport (Streamlit Cloud previews at mobile width)
[ ] secrets.toml not committed (no API keys in this app but good habit)
[ ] README.md has live URL and one-line description
```

**Model loading pattern (critical for performance):**
```python
@st.cache_resource
def load_model():
    # Load LightGBM model
    import lightgbm as lgb
    model = lgb.Booster(model_file='csao_model.txt')
    return model

@st.cache_data
def load_data():
    users  = pd.read_csv('users.csv')
    menu   = pd.read_csv('menu_items.csv')
    orders = pd.read_csv('order_history.csv')
    return users, menu, orders
```

Without `@st.cache_resource`, the model reloads on every single user interaction. The app will feel like it's hanging. This is the single most common Streamlit performance mistake.

---

## FINAL APP STRUCTURE (File Order)

```python
# app.py structure

# 1. Page config (MUST be first)
st.set_page_config(...)

# 2. CSS injection
st.markdown("<style>...</style>", unsafe_allow_html=True)

# 3. Load model and data (cached)
model = load_model()
users, menu, orders = load_data()

# 4. Session state initialization
init_session_state()

# 5. LEFT PANEL — all inputs
with st.sidebar:
    render_profile_selector()
    render_menu_browser()
    render_cart_summary()
    render_generate_button()

# 6. RIGHT PANEL — all outputs
render_kpi_row()
if st.session_state.recommendations is not None:
    render_recommendation_rail()
    render_explainability_panel()
else:
    render_empty_state()
```

---

## RECOMMENDATION RAIL — DISPLAY RULES

### Show Top 5 Only (Not All 8)
The current app shows all 8 candidates in a 4×2 grid. This is wrong for two reasons — it looks like a product catalogue, and it dilutes the confidence signal by showing weak recommendations alongside strong ones.

**Rule:** Show only the top 5 ranked by `predicted_score`. If judges want to see more, an optional "Show all" toggle is fine but default is 5.

```python
# After generating recommendations, slice to top 5
top_recs = recommendations.nlargest(5, 'predicted_score').reset_index(drop=True)
```

### Layout — Horizontal Row, Not Grid
A CSAO rail on a real food app is a single horizontal row of cards, not a grid. The grid layout feels like a search results page. The rail layout feels like a live product.

```python
# 5 columns side by side — horizontal rail
cols = st.columns(5)
for i, (_, rec) in enumerate(top_recs.iterrows()):
    with cols[i]:
        render_rec_card(rec)
```

On narrower viewports this naturally wraps. That's acceptable.

### Card Design — Dark, Not White
Current cards are white on dark background. This creates jarring contrast and looks like default Bootstrap components. Cards should be `#242424` with a colored top border matching the node color — same warm dark family as the rest of the app.

```python
# Top border color = node color, not the card fill
border-top: 3px solid {node_color};
background: #242424;
```

---

## DYNAMIC RAIL — LIVE UPDATES ON CART CHANGE

**This is the most important UX requirement in the entire document.**

The CSAO rail must regenerate automatically every time the cart changes — item added OR item removed. The user should never need to click "Generate" more than once (the first time). After that, every cart modification triggers a silent background regeneration.

### Why This Matters
The entire architecture is built around cart state. When a user adds Vada Pav, Node1 fires and recommends Extra Pav. When they add Extra Pav, the cart now has 2 items, the anchor cuisine is confirmed as Indian Street, AOV headroom shrinks, and Node3 co-occurrence patterns shift. The new rail should reflect this updated state immediately — showing Masala Chaas instead of Extra Pav (already in cart), and potentially activating Node6 if headroom is now tight.

A static rail that doesn't respond to cart changes makes the whole two-stage pipeline invisible to the judge watching.

### The cascade a judge should see:
```
User adds Vada Pav (₹109)
→ Rail shows: Extra Pav, Masala Chaas, Sambar, Lassi, Gulab Jamun

User adds Extra Pav from rail (₹29)  ← clicking + Add on a rec card
→ Rail immediately regenerates
→ Extra Pav disappears from rail (already in cart)
→ Rail now shows: Masala Chaas, Sambar, Lassi, Gulab Jamun, Masala Papad
→ Headroom indicator updates: ₹266 → ₹237

User adds Masala Chaas (₹49)
→ Rail regenerates again
→ Beverage slot now occupied, Node4 shifts to second beverage or dessert
→ Cart value: ₹187, Headroom: ₹188
```

This live cascade is the demo moment. It shows the system is stateful and intelligent, not a one-shot batch process.

### Implementation
```python
# In the + Add button handler (both menu items AND recommendation cards)
if st.button("+ Add", key=f"add_{item_id}"):
    st.session_state.cart[item_id] = item
    # If recommendations have been generated at least once, auto-regenerate
    if st.session_state.get('recommendations_generated', False):
        st.session_state.recommendations = generate_recommendations(
            cart=st.session_state.cart,
            profile=st.session_state.profile,
            model=model,
        )
    st.rerun()

# In the [×] remove button handler
if st.button("×", key=f"remove_{item_id}"):
    del st.session_state.cart[item_id]
    if st.session_state.get('recommendations_generated', False):
        if len(st.session_state.cart) > 0:
            st.session_state.recommendations = generate_recommendations(...)
        else:
            st.session_state.recommendations = None
            st.session_state.recommendations_generated = False
    st.rerun()
```

**Flag to track:** `st.session_state.recommendations_generated = True` is set the first time the user clicks Generate. After that flag is set, every cart change silently regenerates. Before that flag, cart changes just update the cart display without generating (user hasn't asked for recommendations yet).

### Remove the Generate Button after first use
After the first generation, the Generate button should change to a subtle "Regenerating..." spinner that appears briefly on cart changes, then disappears. The explicit button should not require re-clicking.

```python
if not st.session_state.get('recommendations_generated', False):
    # First time — show the big CTA button
    if st.button("⚡ Generate CSAO Rail", use_container_width=True):
        st.session_state.recommendations = generate_recommendations(...)
        st.session_state.recommendations_generated = True
        st.rerun()
else:
    # Already generated — show subtle status instead of button
    st.caption("⚡ Rail updates automatically as you modify your cart")
```

---

## TRANSPARENCY CONSOLE — ENGINE LOG

### Keep This Feature, It's a Differentiator
The existing transparency console showing the Hexagon engine log is genuinely good and most teams won't have it. Do not remove it. It directly answers the judge question "how did you arrive at these recommendations?" without requiring them to ask.

### What to Keep
- Monospace font styling for the log — this is intentional, it looks like an actual engine output
- Per-node candidate count with method label (cuisine-matched + Item2Vec)
- Total candidates generated
- LightGBM scoring section showing features used and candidates scored

### What to Add — Item2Vec Similarity Scores
Currently the console shows candidate counts but not WHY each item was selected within a node. Add the Item2Vec cosine similarity score that drove the selection:

```
HEXAGON CANDIDATE GENERATOR — ENGINE LOG
─────────────────────────────────────────
Anchor Cuisine: Indian Street
Cart Value: ₹109 | Items: 1 | AOV: ₹375
Headroom: ₹266 | Chaos Cart: No

Node1 Extension:  2 candidates (cuisine-matched + Item2Vec)
  → Extra Pav        (Item2Vec similarity: 0.91)
  → Masala Pav       (Item2Vec similarity: 0.87)

Node2 Texture:    1 candidate  (cuisine-matched + Item2Vec)
  → Masala Papad     (Item2Vec similarity: 0.74)

Node3 CoOccur:    1 candidate  (co-purchase + cuisine filter)
  → Masala Chaas     (co-purchase count: 847 orders)

Node4 Beverage:   2 candidates (Item2Vec ranked)
  → Lassi            (Item2Vec similarity: 0.68)
  → Cold Coffee      (Item2Vec similarity: 0.61)

Node5 Dessert:    2 candidates (Item2Vec ranked)
  → Gulab Jamun      (dessert_affinity: 0.72)
  → Kulfi            (dessert_affinity: 0.58)

Node6 Budget:     0 candidates (within ₹133 + Item2Vec)
  → No items found within budget threshold

Total candidates: 8 → LightGBM ranks → Top 5 shown
─────────────────────────────────────────
LIGHTGBM RANKER — SCORING
Features used: 33
Candidates scored: 8
Top score: 0.69 (Extra Pav — Node1)
Inference time: 12ms
```

This single addition validates your Item2Vec claim visually. Judges see the similarity scores and immediately understand the embeddings are doing real work — no t-SNE plot required.

### Placement
Keep as a collapsible `st.expander` below the recommendation rail. Default: **collapsed**. Label: `"🔧 Engine Log (Transparency Console)"`. Judges who want to go deep click it. Casual viewers don't see the raw log cluttering the UI.

```python
with st.expander("🔧 Engine Log (Transparency Console)", expanded=False):
    render_engine_log(st.session_state.engine_log)
```

### Store the log in session state
```python
# In generate_recommendations(), build the log as a string
engine_log = []
engine_log.append(f"Anchor Cuisine: {anchor_cuisine}")
engine_log.append(f"Cart Value: ₹{cart_value} | Items: {n_items} | AOV: ₹{user_aov}")
# ... per node ...
st.session_state.engine_log = "\n".join(engine_log)
```

---

## SUMMARY OF UX IMPROVEMENTS

| Current | New |
|---------|-----|
| 5 dropdowns for profile | Visual cards + toggle pills |
| Multiselect for items | Searchable menu browser with + Add buttons |
| Static cart display | Live cart with remove buttons and headroom indicator |
| Button always enabled | Button disabled until cart has items |
| 8 items in 4×2 grid | Top 5 only in single horizontal rail row |
| White cards on dark bg | Dark `#242424` cards with colored node top-border |
| Rail never updates | Rail auto-regenerates on every cart add/remove |
| Generate button always visible | Disappears after first use, replaced with status caption |
| No explanation of why | Expandable "Why this?" panel per node |
| Transparency console missing Item2Vec detail | Item2Vec similarity scores shown per candidate |
| Transparency console always visible | Collapsed by default, expandable on demand |
| No empty states | Contextual empty states with guidance |
| No latency display | Generation time shown on every run |
| No micro-interactions | Toast notifications, color-coded states |
| Model reloads on every click | `@st.cache_resource` — loads once |

*Hand this entire document to Antigravity. Everything needed to implement is here.*
