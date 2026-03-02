import React, { useState, useEffect, useCallback } from 'react';
import { Utensils, Bell, FlaskConical, ExternalLink } from 'lucide-react';
import PersonaPanel from './components/PersonaPanel';
import RestaurantList from './components/RestaurantList';
import MenuPanel from './components/MenuPanel';
import PairsWellRail from './components/PairsWellRail';
import InsightsPanel from './components/InsightsPanel';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8085';

// ─── Disclaimer Banner ───────────────────────────────────────────────────────
function DisclaimerBanner() {
  const [dismissed, setDismissed] = React.useState(false);
  if (dismissed) return null;
  return (
    <div style={{
      background: 'linear-gradient(135deg, #fffbeb, #fef3c7)',
      border: '1px solid #f59e0b',
      borderRadius: '12px',
      padding: '10px 16px',
      marginBottom: '16px',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      maxWidth: '1600px',
      margin: '0 auto 16px auto',
      width: '100%',
      boxSizing: 'border-box',
    }}>
      <FlaskConical size={18} style={{ color: '#d97706', flexShrink: 0, marginTop: '1px' }} />
      <div style={{ flex: 1, fontSize: '13px', lineHeight: '1.5', color: '#78350f' }}>
        <strong style={{ color: '#92400e' }}>Reference Demo — Not a Production System.</strong>{' '}
        This interactive demo is a <em>conceptual prototype</em> built to illustrate the CSAO Recommendation System's logic
        using a synthetic dataset (1,000 users · 500 restaurants · 9,114 items). It is intended as a visual reference
        for how the Hexagon Engine + LightGBM Ranker would operate, and is{' '}
        <strong>not Zomato's actual recommendation infrastructure</strong>.
        All users, restaurants, and orders are synthetically generated for demonstration purposes only.
        <span style={{ marginLeft: '12px' }}>
          <a href="https://kaggle.com/datasets/navdeepdhunna/csao-dataset-2" target="_blank" rel="noreferrer"
            style={{ color: '#b45309', textDecoration: 'underline', marginRight: '10px' }}>
            📊 Dataset
          </a>
        </span>
      </div>
      <button onClick={() => setDismissed(true)} style={{
        background: 'none', border: 'none', cursor: 'pointer', color: '#92400e',
        fontSize: '18px', lineHeight: 1, padding: '0 4px', flexShrink: 0
      }}>×</button>
    </div>
  );
}

function App() {
  const [profile, setProfile] = useState({
    segment: 'mid',
    is_veg: false,
    city: 'Mumbai',
    meal_time: 'lunch',
  });

  const [cities, setCities] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [selectedRestaurantId, setSelectedRestaurantId] = useState(null);
  const [menu, setMenu] = useState([]);
  const [cart, setCart] = useState([]);
  const [recData, setRecData] = useState(null);
  const [userAov, setUserAov] = useState(450);
  const [cartValue, setCartValue] = useState(0);
  const [headroom, setHeadroom] = useState(450);
  const [engineLog, setEngineLog] = useState([]);
  const [latencyMs, setLatencyMs] = useState(null);

  // Fetch cities on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/cities`)
      .then(r => r.json())
      .then(data => setCities(data))
      .catch(err => console.error('Failed to load cities:', err));
  }, []);

  // Fetch restaurants when city changes
  useEffect(() => {
    fetch(`${API_BASE}/api/restaurants?city=${encodeURIComponent(profile.city)}`)
      .then(r => r.json())
      .then(data => {
        setRestaurants(data);
        if (data.length > 0) {
          setSelectedRestaurantId(data[0].restaurant_id);
        }
      })
      .catch(err => console.error('Failed to load restaurants:', err));
  }, [profile.city]);

  // Fetch menu when restaurant changes
  useEffect(() => {
    if (!selectedRestaurantId) return;
    fetch(`${API_BASE}/api/menu/${selectedRestaurantId}`)
      .then(r => r.json())
      .then(data => setMenu(data))
      .catch(err => console.error('Failed to load menu:', err));
  }, [selectedRestaurantId]);

  // Filtered menu based on veg preference
  const filteredMenu = profile.is_veg ? menu.filter(i => i.is_veg) : menu;

  // Fetch recommendations
  const fetchRecommendations = useCallback(async (currentCart) => {
    if (currentCart.length === 0) {
      setRecData(null);
      setCartValue(0);
      setHeadroom(userAov);
      setEngineLog([]);
      setLatencyMs(null);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          restaurant_id: selectedRestaurantId,
          cart_item_ids: currentCart.map(c => c.item_id),
          profile,
        }),
      });
      const data = await res.json();
      setRecData(data);
      setCartValue(data.cart_value || 0);
      setHeadroom(data.headroom || 0);
      setUserAov(data.user_aov || 450);
      setEngineLog(data.engine_log || []);
      setLatencyMs(data.latency_ms || null);
    } catch (err) {
      console.error('Recommend failed:', err);
    }
  }, [selectedRestaurantId, profile, userAov]);

  const addToCart = useCallback((item) => {
    if (cart.find(c => c.item_id === item.item_id)) return;
    const newCart = [...cart, item];
    setCart(newCart);
    fetchRecommendations(newCart);
  }, [cart, fetchRecommendations]);

  const removeFromCart = useCallback((itemId) => {
    const newCart = cart.filter(c => c.item_id !== itemId);
    setCart(newCart);
    fetchRecommendations(newCart);
  }, [cart, fetchRecommendations]);

  const handleProfileChange = useCallback((key, val) => {
    const newProfile = { ...profile, [key]: val };
    setProfile(newProfile);
    if (key === 'city') {
      // City change: clear everything, restaurants will re-fetch via useEffect
      setCart([]);
      setRecData(null);
      setCartValue(0);
      setHeadroom(userAov);
      setEngineLog([]);
      setLatencyMs(null);
    } else if (key === 'is_veg') {
      setCart([]);
      setRecData(null);
      setCartValue(0);
      setHeadroom(userAov);
      setEngineLog([]);
      setLatencyMs(null);
    } else if (cart.length > 0) {
      setTimeout(() => fetchRecommendations(cart), 50);
    }
  }, [profile, cart, fetchRecommendations, userAov]);

  const handleSelectRestaurant = useCallback((restId) => {
    setSelectedRestaurantId(restId);
    setCart([]);
    setRecData(null);
    setCartValue(0);
    setHeadroom(userAov);
    setEngineLog([]);
    setLatencyMs(null);
  }, [userAov]);

  const recommendations = recData?.recommendations || [];

  return (
    <div className="min-h-screen p-4 md:p-6 flex flex-col" style={{ background: 'var(--color-zomato-light)' }}>
      {/* HEADER */}
      <header className="flex justify-between items-center mb-6 max-w-[1600px] mx-auto w-full">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg"
            style={{ background: 'var(--color-zomato-red)', boxShadow: '0 4px 14px rgba(226,55,68,0.3)' }}>
            <Utensils size={20} strokeWidth={2.5} />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: 'var(--color-zomato-charcoal)' }}>
            Carto
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <button className="p-2.5 rounded-xl bg-white border border-[#EAEAEA] text-gray-500 hover:text-[#E23744] transition-colors">
            <Bell size={20} />
          </button>
          <div className="h-10 w-10 rounded-xl overflow-hidden ring-2 ring-white shadow-sm"
            style={{ background: 'linear-gradient(135deg, #F5B800, #E23744)' }}>
            <div className="w-full h-full flex items-center justify-center text-white font-bold text-sm">U</div>
          </div>
        </div>
      </header>

      {/* DISCLAIMER */}
      <DisclaimerBanner />

      {/* MAIN GRID */}
      <main className="grid grid-cols-12 gap-6 flex-grow max-w-[1600px] mx-auto w-full pb-4">
        {/* LEFT: Persona + Cart */}
        <div className="col-span-12 lg:col-span-3 flex flex-col gap-5">
          <PersonaPanel
            profile={profile}
            onProfileChange={handleProfileChange}
            cart={cart}
            onRemoveFromCart={removeFromCart}
            cartValue={cartValue}
            headroom={headroom}
            cities={cities}
          />
        </div>

        {/* CENTER: Restaurants + Menu + Rail */}
        <div className="col-span-12 lg:col-span-6 flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6" style={{ height: '500px' }}>
            <RestaurantList
              restaurants={restaurants}
              selectedId={selectedRestaurantId}
              onSelect={handleSelectRestaurant}
            />
            <MenuPanel
              menu={filteredMenu}
              cart={cart}
              onAddToCart={addToCart}
              selectedRestaurantId={selectedRestaurantId}
            />
          </div>
          <PairsWellRail
            recommendations={recommendations}
            cart={cart}
            onAddToCart={addToCart}
            latencyMs={latencyMs}
          />
        </div>

        {/* RIGHT: Insights */}
        <div className="col-span-12 lg:col-span-3">
          <InsightsPanel
            recommendations={recommendations}
            cart={cart}
            engineLog={engineLog}
            latencyMs={latencyMs}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
