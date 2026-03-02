import re

with open("app.py", "r", encoding="utf-8") as f:
    app_py_code = f.read()

# ── 1. Update Custom CSS for the Exact Dashboard Layout Match ──
# We will inject the new CSS that combines the structure from csao_dashboard_improved.html
# and the glassmorphism design system.
new_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
.stDeployButton { display: none; }

/* Remove default padding to allow full bleed */
.block-container { 
    padding: 0 !important; 
    max-width: 100% !important;
    overflow: hidden !important;
}

/* Base Body and Background */
.stApp { 
    background-color: #0F0F0F; 
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(245, 184, 0, 0.05) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(91, 168, 176, 0.05) 0%, transparent 40%);
    background-attachment: fixed;
    height: 100vh;
    overflow: hidden;
}
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
    z-index: 9999;
}

/* Main text color */
p, span, label, h1, h2, h3, h4, div { color: #F5F5F5; }

/* --- TWO PANEL LAYOUT OVERRIDES --- */

/* Sidebar Override */
[data-testid="stSidebar"] {
    background-color: rgba(26, 26, 26, 0.6) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    width: 380px !important;
    min-width: 380px !important;
    max-width: 380px !important;
    padding: 0 !important;
}

/* Custom internal padding for sidebar sections */
.sidebar-section {
    padding: 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.st-emotion-cache-16txtl3 {
    padding: 2rem 1rem;
}

/* Header style inside sidebar */
.sidebar-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 8px;
}
.header-icon {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background-color: #F5B800;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}
.header-title { font-size: 16px; font-weight: 700; letter-spacing: -0.3px; line-height: 1.2; margin:0;}
.header-sub { font-size: 11px; color: #8A8A8A; margin:0;}

/* Main Panel Adjustments */
/* Make it scrollable independently */
.main-content-scrollable {
    height: 100vh;
    overflow-y: auto;
    padding: 32px;
    padding-bottom: 100px;
}

/* Section Title */
.section-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #8A8A8A;
    margin-bottom: 16px;
    display: block;
}

/* Label */
.input-label {
    font-size: 12px;
    color: #8A8A8A;
    margin-bottom: 8px;
    display: block;
}

/* Profile Segment Cards */
.segment-grid {
    display: grid;
    grid-template-cols: 1fr 1fr 1fr;
    gap: 8px;
    margin-bottom: 16px;
}
.segment-btn {
    background: rgba(26, 26, 26, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
}
.segment-btn:hover { border-color: rgba(255, 255, 255, 0.2); }
.segment-btn.active {
    background: rgba(245, 184, 0, 0.1);
    border: 1px solid #F5B800;
}
.segment-btn.active .segment-name { color: #F5B800; }

.segment-name { font-size: 12px; font-weight: 600; color: #F5F5F5; margin-bottom: 4px; }
.segment-val { font-size: 10px; color: #8A8A8A; }

/* Diet Pills */
.diet-grid { display: grid; grid-template-cols: 1fr 1fr; gap: 8px; margin-bottom: 16px;}
.diet-btn {
    background: rgba(26, 26, 26, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 8px 12px;
    text-align: center;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    color: #8A8A8A;
}
.diet-btn.active-veg { background: rgba(34, 197, 94, 0.1); border-color: #22C55E; color: #22C55E; }
.diet-btn.active-nv { background: rgba(239, 68, 68, 0.1); border-color: #EF4444; color: #EF4444; }

/* Streamlit Selectbox Override */
div[data-baseweb="select"] > div {
    background-color: rgba(26, 26, 26, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    color: #F5F5F5 !important;
}

/* Menu Items List */
.menu-item {
    background: rgba(26, 26, 26, 0.4);
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s;
}
.menu-item:hover {
    border-color: rgba(91, 168, 176, 0.3);
    background: rgba(26, 26, 26, 0.6);
}
.menu-item-left { display: flex; gap: 12px; align-items: center; }
.menu-item-dot { width: 8px; height: 8px; border-radius: 50%; }
.menu-item-name { font-size: 13px; font-weight: 500; color: #F5F5F5; }
.menu-item-price { font-size: 11px; color: #8A8A8A; margin-top: 2px;}
.menu-item-add {
    width: 28px; height: 28px;
    border-radius: 8px;
    background: rgba(245, 184, 0, 0.1);
    color: #F5B800;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; cursor: pointer; border: none;
}
.menu-item-add:hover { background: #F5B800; color: #1A1A1A; transform: scale(1.05); }

/* Sticky Cart Bottom */
.sticky-cart {
    background: rgba(15, 15, 15, 0.95);
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 24px;
    margin-top: auto;
}
.cart-list-item {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 13px; color: #8A8A8A; margin-bottom: 8px;
}
.cart-list-price { font-weight: 500; color: #F5F5F5; }
.cart-remove {
    background: transparent; border: none; color: #EF4444; font-size: 16px; cursor: pointer; padding: 0 4px;
}

.cart-totals { border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; margin-top: 12px; margin-bottom: 16px; }
.cart-total-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }
.cart-total-label { color: #8A8A8A; }
.cart-total-val { font-weight: 600; color: #F5F5F5; }
.cart-total-val.accent { color: #F5B800; }

.btn-primary {
    width: 100%;
    background: linear-gradient(135deg, #F5B800 0%, #E5A800 100%);
    color: #1A1A1A;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 4px 16px rgba(245, 184, 0, 0.3);
}
.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(245, 184, 0, 0.4);
}

/* ------------- MAIN PANEL ------------- */

/* KPI Row Grid */
.kpi-grid { display: grid; grid-template-cols: 1fr 1fr 1fr 1fr; gap: 16px; margin-bottom: 32px; }
.kpi-card {
    background: rgba(26, 26, 26, 0.5);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}
.kpi-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.kpi-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #8A8A8A; }
.kpi-icon {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.kpi-val-row { display: flex; align-items: baseline; gap: 8px; }
.kpi-main-val { font-size: 28px; font-weight: 700; color: #F5F5F5; letter-spacing: -0.5px; }
.kpi-sub-val { font-size: 12px; font-weight: 500;}
.kpi-desc { font-size: 11px; color: #8A8A8A; margin-top: 4px; }

/* 5-Column Recommendation Grid */
.rec-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; }
.rec-header h2 { font-size: 20px; font-weight: 700; color: #F5F5F5; margin: 0 0 4px 0; letter-spacing: -0.3px;}
.rec-header p { font-size: 13px; color: #8A8A8A; margin: 0; }
.rec-meta { font-size: 12px; color: #8A8A8A; display: flex; align-items: center; gap: 12px; }

.rec-grid { display: grid; grid-template-cols: repeat(5, 1fr); gap: 16px; margin-bottom: 32px; }
.rec-card {
    background: linear-gradient(135deg, rgba(40,40,40,0.8) 0%, rgba(26,26,26,0.6) 100%);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    transition: all 0.3s;
    display: flex;
    flex-direction: column;
}
.rec-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}
.rec-top-border { height: 4px; width: 100%; }
.rec-content { padding: 16px; flex: 1; display: flex; flex-direction: column; }
.rec-badge-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.rec-badge { font-size: 10px; font-weight: 600; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.rec-rank { font-size: 11px; font-weight: 700; color: #8A8A8A; }

.rec-name { font-size: 14px; font-weight: 600; color: #F5F5F5; margin: 0 0 4px 0; line-height: 1.3;}
.rec-price { font-size: 20px; font-weight: 700; color: #F5F5F5; margin: 0 0 24px 0; }

.rec-conf-row { display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px; }
.rec-conf-label { color: #8A8A8A; }
.rec-conf-val { font-weight: 600; color: #D4E5E8; }
.rec-bar-bg { background: rgba(255,255,255,0.05); height: 4px; border-radius: 2px; width: 100%; overflow: hidden; margin-bottom: 20px;}
.rec-bar-fill { height: 100%; border-radius: 2px; }

.rec-add-btn {
    background: rgba(255,255,255,0.05);
    border: none;
    border-radius: 8px;
    padding: 10px;
    width: 100%;
    color: #F5F5F5;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: auto;
}
.rec-add-btn:hover { background: rgba(245, 184, 0, 0.15); color: #F5B800; }

/* Insights / Log Box */
.insights-box {
    background: rgba(26, 26, 26, 0.5);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 20px;
}

/* Footer */
.app-footer {
    position: fixed;
    bottom: 0;
    left: 380px; /* offset by sidebar */
    right: 0;
    background: rgba(15, 15, 15, 0.9);
    backdrop-filter: blur(10px);
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 12px 32px;
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #8A8A8A;
    z-index: 100;
}

/* Hide streamlit default button styles where we use custom HTML */
div[data-testid="stButton"] { width: 100%; }
div[data-testid="stButton"] button {
    width: 100%;
}
</style>
"""

# Find the start of the CSS injection and replace it.
css_start_idx = app_py_code.find("<style>")
css_end_idx = app_py_code.find("</style>") + 8

app_py_code = app_py_code[:css_start_idx] + new_css + app_py_code[css_end_idx:]


# ── 2. REWRITE STREAMLIT LAYOUT TO MATCH DASHBOARD Exactly ──
# We extract everything from "LEFT PANEL" downwards and replace it.

left_panel_idx = app_py_code.find("# LEFT PANEL — SIDEBAR (All Inputs)")

layout_code = """# ─────────────────────────────────────────────────────────────────────────────
# TWO-PANEL DASHBOARD LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

# Inject raw HTML structure for the Sidebar + Main Layout to get the exact HTML dashboard styling
# Since we need interactivity (buttons, selects), we use a mixture of st.sidebar for inputs
# and st.container for main area.

# Hide default sidebar completely using CSS, we'll build our own inside the default st.sidebar area
# Actually, the best way to get exact match is to use the standard st.sidebar but style it with the CSS above.

with st.sidebar:
    # --- Sidebar Header ---
    st.markdown('''
    <div class="sidebar-section" style="padding-top: 32px;">
        <div class="sidebar-header">
            <div class="header-icon">🛍️</div>
            <div>
                <p class="header-title">CSAO Recommendations</p>
                <p class="header-sub">Cart Add-On System</p>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # --- Profile Section ---
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<span class="section-title">User Profile</span>', unsafe_allow_html=True)
    
    st.markdown('<span class="input-label">User Segment</span>', unsafe_allow_html=True)
    
    # Use standard Streamlit buttons but style them transparently to act as triggers
    # Or just use radio button styled via CSS. To keep it robust, we'll use columns + buttons.
    seg_cols = st.columns(3)
    segments = [("Budget", "~₹200"), ("Mid", "~₹450"), ("Premium", "~₹750")]
    for i, (label, val) in enumerate(segments):
        with seg_cols[i]:
            btn_key = f"seg_{label}"
            # Invisible streamlit button over the HTML
            if st.button(label, key=btn_key):
                st.session_state.profile['segment'] = label.lower()
                if st.session_state.recommendations_generated:
                    run_recommendation_pipeline()
                st.rerun()
            
            # The visual representation
            active_class = "active" if st.session_state.profile['segment'] == label.lower() else ""
            html = f'''<div class="segment-btn {active_class}" style="margin-top: -45px; pointer-events: none;">
                <div class="segment-name">{label}</div>
                <div class="segment-val">{val}</div>
            </div>'''
            st.markdown(html, unsafe_allow_html=True)
            
    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
    
    # Dietary Preference
    st.markdown('<span class="input-label">Dietary Preference</span>', unsafe_allow_html=True)
    diet_cols = st.columns(2)
    with diet_cols[0]:
        if st.button("Vegetarian", key="diet_veg"):
            st.session_state.profile['is_veg'] = True
            st.session_state.cart = {}
            st.session_state.recommendations = None
            st.session_state.recommendations_generated = False
            st.rerun()
        active = "active-veg" if st.session_state.profile['is_veg'] else ""
        st.markdown(f'<div class="diet-btn {active}" style="margin-top:-45px; pointer-events:none;">Vegetarian</div>', unsafe_allow_html=True)
        
    with diet_cols[1]:
        if st.button("Non-Veg", key="diet_nv"):
            st.session_state.profile['is_veg'] = False
            st.session_state.cart = {}
            st.session_state.recommendations = None
            st.session_state.recommendations_generated = False
            st.rerun()
        active = "active-nv" if not st.session_state.profile['is_veg'] else ""
        st.markdown(f'<div class="diet-btn {active}" style="margin-top:-45px; pointer-events:none;">Non-Veg</div>', unsafe_allow_html=True)

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
    
    # Meal Time
    st.markdown('<span class="input-label">Meal Time</span>', unsafe_allow_html=True)
    
    # Map index
    times = ["Lunch (12:00 PM - 3:00 PM)", "Dinner (7:00 PM - 11:00 PM)", "Snacks (4:00 PM - 6:00 PM)", "Breakfast (8:00 AM - 11:00 AM)"]
    time_keys = ["lunch", "dinner", "evening_snack", "breakfast"]
    current_time_str = st.session_state.profile.get('meal_time', 'lunch')
    try:
        def_idx = time_keys.index(current_time_str)
    except:
        def_idx = 0
        
    selected_time = st.selectbox("Meal Time", times, index=def_idx, label_visibility="collapsed")
    new_time_key = time_keys[times.index(selected_time)]
    if new_time_key != current_time_str:
        st.session_state.profile['meal_time'] = new_time_key
        if st.session_state.recommendations_generated:
            run_recommendation_pipeline()
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- Current Cart Section ---
    st.markdown('<div class="sidebar-section" style="flex:1; border-bottom: none;">', unsafe_allow_html=True)
    st.markdown('<span class="section-title">Current Cart</span>', unsafe_allow_html=True)
    st.markdown('<span class="input-label">Restaurant</span>', unsafe_allow_html=True)
    
    city_rests = rests[rests["city"] == st.session_state.profile['city']].copy()
    rest_options = city_rests[["restaurant_id", "name", "cuisine_primary"]].copy()
    rest_options["display"] = rest_options["name"] + " · " + rest_options["cuisine_primary"]
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

        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
        
        # Mini Menu Browser
        rest_menu_full = menu[menu["restaurant_id"] == rid].copy()
        if st.session_state.profile['is_veg']:
            rest_menu_display = rest_menu_full[rest_menu_full["is_veg"] == True]
        else:
            rest_menu_display = rest_menu_full
            
        mains = rest_menu_display[rest_menu_display["category"] == "Main"].head(5)
        others = rest_menu_display[rest_menu_display["category"] != "Main"].head(5)
        filtered_menu = pd.concat([mains, others])
        
        # Render Menu items
        for _, item in filtered_menu.iterrows():
            item_id = item["item_id"]
            if item_id in st.session_state.cart: continue
            
            veg_dot = "#22C55E" if item["is_veg"] else "#EF4444"
            st.markdown(f'''
            <div class="menu-item">
                <div class="menu-item-left">
                    <div class="menu-item-dot" style="background-color: {veg_dot}"></div>
                    <div>
                        <div class="menu-item-name">{item['item_name']}</div>
                        <div class="menu-item-price">₹{item['price']:.0f}</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Add Button Overlay
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("➕", key=f"add_{item_id}"):
                    st.session_state.cart[item_id] = item.to_dict()
                    st.toast(f"✓ {item['item_name']} added", icon="🛒")
                    if st.session_state.recommendations_generated:
                        run_recommendation_pipeline()
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- Sticky Cart Bottom ---
    st.markdown('<div class="sticky-cart">', unsafe_allow_html=True)
    
    cart_total = 0
    if len(st.session_state.cart) > 0:
        for iid, idata in st.session_state.cart.items():
            cart_total += idata["price"]
            st.markdown(f'''
            <div class="cart-list-item">
                <span>{idata["item_name"]}</span>
                <span class="cart-list-price">₹{idata["price"]:.0f}</span>
            </div>
            ''', unsafe_allow_html=True)
            
            # Remove Button Overlays
            if st.button("remove", key=f"rm_{iid}"):
                del st.session_state.cart[iid]
                if st.session_state.recommendations_generated:
                    if len(st.session_state.cart) > 0: run_recommendation_pipeline()
                    else:
                        st.session_state.recommendations = None
                        st.session_state.recommendations_generated = False
                st.rerun()
                
        # Get user AOV
        profile = st.session_state.profile
        matching = users[(users["city"] == profile['city']) & (users["user_segment"] == profile['segment']) & (users["is_veg"] == profile['is_veg'])]
        user_aov = matching.iloc[0]["historical_aov"] if len(matching) > 0 else 400
        headroom = max(0, user_aov - cart_total)
        
        st.markdown(f'''
        <div class="cart-totals">
            <div class="cart-total-row">
                <span class="cart-total-label">Subtotal</span>
                <span class="cart-total-val">₹{cart_total:.0f}</span>
            </div>
            <div class="cart-total-row">
                <span class="cart-total-label">Items</span>
                <span class="cart-total-val">{len(st.session_state.cart)}</span>
            </div>
            <div class="cart-total-row">
                <span class="cart-total-label" style="color:#5BA8B0;">Available Budget</span>
                <span class="cart-total-val accent" style="color:#5BA8B0;">₹{headroom:.0f}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button("↻ Update Recommendations", key="gen_btn"):
            run_recommendation_pipeline()
            st.rerun()
    else:
        st.markdown('<div style="text-align:center; color:#8A8A8A; font-size:13px; padding: 20px;">Cart is empty</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

# ── MAIN CONTENT AREA ──
st.markdown('<div class="main-content-scrollable">', unsafe_allow_html=True)

if len(st.session_state.cart) > 0:
    cart_items = pd.DataFrame(st.session_state.cart.values())
    cart_total = cart_items["price"].sum()
    profile = st.session_state.profile
    matching = users[(users["city"] == profile['city']) & (users["user_segment"] == profile['segment']) & (users["is_veg"] == profile['is_veg'])]
    user_aov = matching.iloc[0]["historical_aov"] if len(matching) > 0 else 400
    headroom = max(0, user_aov - cart_total)

    # 1. KPI Grid
    hr_color = "#22C55E" if headroom > 200 else "#F5B800" if headroom > 50 else "#EF4444"
    st.markdown(f'''
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-title">Cart Value</span>
                <div class="kpi-icon" style="background: rgba(239, 68, 68, 0.1); color: #EF4444;">🛒</div>
            </div>
            <div class="kpi-val-row">
                <span class="kpi-main-val">₹{cart_total:.0f}</span>
                <span class="kpi-sub-val" style="color: #22C55E;">+15%</span>
            </div>
            <div class="kpi-desc">vs. avg session</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-title">User AOV</span>
                <div class="kpi-icon" style="background: rgba(59, 130, 246, 0.1); color: #3b82f6;">👤</div>
            </div>
            <div class="kpi-val-row">
                <span class="kpi-main-val">₹{user_aov:.0f}</span>
                <span class="kpi-sub-val" style="color: #8A8A8A; font-weight:400;">historical</span>
            </div>
            <div class="kpi-desc">{st.session_state.profile['segment'].title()} tier segment</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-title">Headroom</span>
                <div class="kpi-icon" style="background: rgba(34, 197, 94, 0.1); color: #22C55E;">↗</div>
            </div>
            <div class="kpi-val-row">
                <span class="kpi-main-val" style="color: {hr_color};">₹{headroom:.0f}</span>
            </div>
            <div class="kpi-desc">Available budget</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-title">Acceptance</span>
                <div class="kpi-icon" style="background: rgba(168, 85, 247, 0.1); color: #a855f7;">✨</div>
            </div>
            <div class="kpi-val-row">
                <span class="kpi-main-val">47.9%</span>
            </div>
            <div class="kpi-desc">Model accuracy</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # 2. Recommendation Rail
    if st.session_state.recommendations is not None and len(st.session_state.recommendations) > 0:
        cdf = st.session_state.recommendations
        top_recs = cdf.nlargest(5, 'score').reset_index(drop=True)
        gen_time = st.session_state.generation_time_ms

        st.markdown(f'''
        <div class="rec-header">
            <div>
                <h2>Recommended Add-Ons</h2>
                <p>Based on order patterns and user preferences</p>
            </div>
            <div class="rec-meta">
                <span><span style="color:#22C55E;">✓</span> Model: LightGBM v2.4</span>
                <span>•</span>
                <span>Latency: {gen_time:.0f}ms</span>
            </div>
        </div>
        <div class="rec-grid">
        ''', unsafe_allow_html=True)
        
        # We need to mix HTML and Streamlit cols for buttons
        cols = st.columns(5)
        for i, (_, rec) in enumerate(top_recs.iterrows()):
            with cols[i]:
                node = rec['hexagon_node']
                node_label = node.split('_', 1)[1] if '_' in node else node
                
                # Match document colors exactly
                colors = {
                    "Extension": "#F5B800",
                    "Texture": "#A78BFA",
                    "Beverage": "#38BDF8",
                    "Dessert": "#34D399",
                    "BudgetHabit": "#EF4444",
                    "CoOccurrence": "#5BA8B0"
                }
                c = colors.get(node_label, "#F5B800")
                conf = int(rec['score'] * 100)
                
                st.markdown(f'''
                <div class="rec-card" style="margin-top:-60px;">
                    <div class="rec-top-border" style="background: {c};"></div>
                    <div class="rec-content">
                        <div class="rec-badge-row">
                            <span class="rec-badge" style="background: {c}20; color: {c}; border: 1px solid {c}40;">{node_label}</span>
                            <span class="rec-rank">#{i+1}</span>
                        </div>
                        <h3 class="rec-name">{rec['item_name']}</h3>
                        <p class="rec-price">₹{rec['price']:.0f}</p>
                        
                        <div style="margin-top:auto;">
                            <div class="rec-conf-row">
                                <span class="rec-conf-label">Confidence</span>
                                <span class="rec-conf-val" style="color:{c};">{conf}%</span>
                            </div>
                            <div class="rec-bar-bg">
                                <div class="rec-bar-fill" style="background: {c}; width: {conf}%;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                rec_item_id = rec['item_id']
                if rec_item_id not in st.session_state.cart:
                    if st.button("Add to Cart", key=f"rec_add_{rec_item_id}"):
                        item_data = menu[menu["item_id"] == rec_item_id].iloc[0].to_dict()
                        st.session_state.cart[rec_item_id] = item_data
                        run_recommendation_pipeline()
                        st.rerun()
                else:
                    st.button("In Cart ✓", key=f"rec_add_{rec_item_id}", disabled=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. Insights Expanders
        st.markdown('<div class="insights-box">', unsafe_allow_html=True)
        with st.expander("📈 Recommendation Insights"):
            st.markdown("Hexagon breakdown based on the UI Analysis document.")
            for node_name in top_recs['hexagon_node'].unique():
                node_items = top_recs[top_recs['hexagon_node'] == node_name]
                st.markdown(f"- **{node_name}**: {', '.join(node_items['item_name'].tolist())}")
        with st.expander("🔧 Engine Log"):
            for l in st.session_state.engine_log:
                st.markdown(l, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # Empty State Main Area
    st.markdown('''
    <div style="height: 100%; display: flex; align-items: center; justify-content: center; opacity: 0.6; padding-top: 100px;">
        <div style="text-align: center;">
            <div style="font-size: 64px; margin-bottom: 24px;">✨</div>
            <h2 style="font-size: 24px; font-weight: 700; color: #F5F5F5; margin-bottom: 8px;">Build your cart</h2>
            <p style="color: #8A8A8A;">Add items from the sidebar menu to see personalized recommendations.</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ──
st.markdown('''
<div class="app-footer">
    <div>CSAO Recommendation System v2.4 • Hexagon + LightGBM Architecture • AUC: 0.7741 (+31.4% vs baseline)</div>
    <div style="color: #22C55E; display: flex; align-items: center; gap: 8px;">
        <div style="width: 8px; height: 8px; background: #22C55E; border-radius: 50%;"></div> System Active
    </div>
</div>
''', unsafe_allow_html=True)
"""

app_py_code = app_py_code[:left_panel_idx] + layout_code

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_py_code)

print("Rewrote layout applied.")
