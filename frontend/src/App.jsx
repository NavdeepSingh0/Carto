import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShoppingCart, Plus, Minus, X, Info } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const NODE_COLORS = {
  "Node1_Extension":    "#F5A623",
  "Node2_Texture":      "#A78BFA",
  "Node3_CoOccurrence": "#38BDF8",
  "Node4_Beverage":     "#34D399",
  "Node5_Dessert":      "#F472B6",
  "Node6_BudgetHabit":  "#FB923C",
};

function App() {
  const [restaurants, setRestaurants] = useState([]);
  const [selectedRest, setSelectedRest] = useState('');
  const [menu, setMenu] = useState([]);
  const [selectedMenuItem, setSelectedMenuItem] = useState('');
  
  const [cart, setCart] = useState([]);
  const [recs, setRecs] = useState(null);
  
  const [profile, setProfile] = useState({
    segment: 'mid',
    is_veg: false,
    city: 'Mumbai',
    meal_time: 'lunch'
  });

  const [insight, setInsight] = useState({ user_aov: 450, cart_value: 0, headroom: 450 });

  useEffect(() => {
    axios.get(`${API_BASE}/restaurants`).then(res => {
      setRestaurants(res.data);
      if (res.data.length > 0) setSelectedRest(res.data[0].restaurant_id);
    });
  }, []);

  useEffect(() => {
    if (selectedRest) {
      axios.get(`${API_BASE}/menu/${selectedRest}`).then(res => {
        setMenu(res.data.filter(i => profile.is_veg ? i.is_veg : true));
        if (res.data.length > 0) setSelectedMenuItem(res.data[0].item_id);
      });
    }
  }, [selectedRest, profile.is_veg]);

  const fetchRecommendations = async (currentCart) => {
    if (currentCart.length === 0) {
      setRecs(null);
      setInsight({ user_aov: 450, cart_value: 0, headroom: 450 });
      return;
    }
    try {
      const res = await axios.post(`${API_BASE}/recommend`, {
        restaurant_id: selectedRest,
        cart_item_ids: currentCart.map(c => c.item_id),
        profile: profile
      });
      setRecs(res.data.recommendations);
      setInsight({
        user_aov: res.data.user_aov,
        cart_value: res.data.cart_value,
        headroom: res.data.headroom
      });
    } catch(err) {
      console.error(err);
    }
  };

  const addToCart = (item) => {
    if (cart.find(c => c.item_id === item.item_id)) return;
    const newCart = [...cart, item];
    setCart(newCart);
    fetchRecommendations(newCart);
  };

  const removeFromCart = (itemId) => {
    const newCart = cart.filter(c => c.item_id !== itemId);
    setCart(newCart);
    fetchRecommendations(newCart);
  };

  const handleProfileChange = (key, val) => {
    const p = { ...profile, [key]: val };
    setProfile(p);
    fetchRecommendations(cart); // recalculate on profile change
  };

  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        <div className="sidebar-scroll">
          <div className="sidebar-header">
            <div className="header-icon">🛍️</div>
            <div>
              <p className="header-title">CSAO Recommendations</p>
              <p className="header-sub">Cart Add-On System</p>
            </div>
          </div>
          
          <hr className="section-divider" />
          <span className="section-label">User Profile</span>
          
          <span className="input-label">User Segment</span>
          <div className="row">
            {['Budget', 'Mid', 'Premium'].map(s => (
              <div key={s} className="col">
                <div 
                  className={`seg-card ${profile.segment === s.toLowerCase() ? 'active' : ''}`}
                  onClick={() => handleProfileChange('segment', s.toLowerCase())}
                >
                  <div className="seg-name">{s}</div>
                  <div className="seg-val">
                    {s === 'Budget' ? '~₹200' : s === 'Mid' ? '~₹450' : '~₹750'}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <span className="input-label">Dietary Preference</span>
          <div className="row">
            <div className="col">
              <div className={`diet-pill ${profile.is_veg ? 'active' : ''}`} onClick={() => { handleProfileChange('is_veg', true); setCart([]); }}>Vegetarian</div>
            </div>
            <div className="col">
              <div className={`diet-pill ${!profile.is_veg ? 'active' : ''}`} onClick={() => { handleProfileChange('is_veg', false); setCart([]); }}>Non-Veg</div>
            </div>
          </div>

          <span className="input-label">Meal Time</span>
          <div className="dark-select-wrapper">
            <select className="dark-select" value={profile.meal_time} onChange={(e) => handleProfileChange('meal_time', e.target.value)}>
              <option value="breakfast">Breakfast (8:00 AM - 11:00 AM)</option>
              <option value="lunch">Lunch (12:00 PM - 3:00 PM)</option>
              <option value="evening_snack">Snacks (4:00 PM - 6:00 PM)</option>
              <option value="dinner">Dinner (7:00 PM - 11:00 PM)</option>
            </select>
          </div>

          <hr className="section-divider" />
          <span className="section-label">Order Context</span>
          
          <span className="input-label">Restaurant</span>
          <select value={selectedRest} onChange={e => { setSelectedRest(e.target.value); setCart([]); }}>
            {restaurants.map(r => <option key={r.restaurant_id} value={r.restaurant_id}>{r.name}</option>)}
          </select>

          <span className="input-label">Add Item to Cart</span>
          <div className="row" style={{marginTop:'8px'}}>
            <select style={{flex:1}} value={selectedMenuItem} onChange={e => setSelectedMenuItem(e.target.value)}>
              {menu.map(m => <option key={m.item_id} value={m.item_id}>{m.item_name} (₹{m.price})</option>)}
            </select>
            <button className="btn-primary" style={{width:'40px', padding:'0', display:'flex', alignItems:'center', justifyContent:'center'}} onClick={() => {
              const m = menu.find(x => x.item_id === selectedMenuItem);
              if (m) addToCart(m);
            }}>
              <Plus size={20} color="#fff" strokeWidth={3}/>
            </button>
          </div>

          {/* CART SUMMARY */}
          {cart.length > 0 && (
            <div className="cart-summary">
              <div className="cart-title">🛒 YOUR CART</div>
              {cart.map(c => (
                <div key={c.item_id} className="cart-item">
                  <div className="cart-item-name">
                    <div className={`diet-dot ${c.is_veg ? 'dot-veg' : 'dot-nv'}`}></div>
                    {c.item_name}
                  </div>
                  <div style={{display:'flex', alignItems:'center'}}>
                    ₹{c.price}
                    <button className="cart-item-remove" onClick={() => removeFromCart(c.item_id)}>
                      <X size={16} />
                    </button>
                  </div>
                </div>
              ))}
              <div className="cart-divider"></div>
              <div className="cart-row-total">
                <span>Subtotal</span>
                <span>₹{insight.cart_value.toFixed(0)}</span>
              </div>
              <div className="cart-row">
                <span>Items</span>
                <span>{cart.length}</span>
              </div>
              <div className="cart-row">
                <span className={insight.headroom > 0 ? 'text-green' : 'text-red'}>Budget Left</span>
                <span className={insight.headroom > 0 ? 'text-green' : 'text-red'}>₹{insight.headroom.toFixed(0)}</span>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="main-content">
        
        {/* KPIs */}
        <div className="kpi-row">
          <div className="kpi-card">
            <div className="kpi-icon">🛒</div>
            <div className="kpi-val">₹{insight.cart_value.toFixed(0)}</div>
            <div className="kpi-label">Cart Value</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon">📊</div>
            <div className="kpi-val">₹{insight.user_aov.toFixed(0)}</div>
            <div className="kpi-label">User AOV</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon">💰</div>
            <div className="kpi-val" style={{color: insight.headroom > 50 ? '#22C55E' : '#EF4444'}}>₹{insight.headroom.toFixed(0)}</div>
            <div className="kpi-label">Headroom</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon">📦</div>
            <div className="kpi-val">{cart.length}</div>
            <div className="kpi-label">Items</div>
          </div>
        </div>

        {cart.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🛒</div>
            <div className="empty-title">Your cart is empty</div>
            <div className="empty-sub">Add some items from the sidebar to see recommendations.</div>
          </div>
        ) : recs && recs.length > 0 ? (
          <>
            <div className="section-header">
              <div>
                <div className="section-title-main">Recommended Add-Ons</div>
                <div className="section-subtitle">Based on order patterns and user preferences</div>
              </div>
              <div className="engine-status">
                <span>✅ Python LightGBM Engine</span>
              </div>
            </div>
            
            <div className="recs-grid">
              {recs.map((rank, idx) => {
                const nodeLabel = rank.hexagon_node.includes('_') ? rank.hexagon_node.split('_')[1] : rank.hexagon_node;
                const conf = Math.round(rank.score * 100);
                const color = NODE_COLORS[rank.hexagon_node] || '#888';
                const inCart = cart.some(c => c.item_id === rank.item_id);

                return (
                  <div key={rank.item_id} className="rec-card">
                    <div className="rec-header">
                      <span className="rec-badge" style={{background: `${color}15`, color: color}}>{nodeLabel}</span>
                      <span className="rec-rank">#{idx+1}</span>
                    </div>
                    
                    <div className="rec-name">{rank.item_name}</div>
                    <div className="rec-price">₹{rank.price.toFixed(0)}</div>
                    
                    <div className="conf-label">Confidence: {conf}%</div>
                    <div className="conf-bg">
                      <div className="conf-fill" style={{width: `${conf}%`, background: color}}></div>
                    </div>

                    {inCart ? (
                      <div className="rec-added">✓ In Cart</div>
                    ) : (
                      <button className="rec-add-btn" onClick={() => addToCart(rank)}>
                        Add to Cart
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">⚡</div>
            <div className="empty-title">Ready to discover?</div>
            <div className="empty-sub">Add more items to generate candidates.</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
