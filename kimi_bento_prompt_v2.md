# Zomato ML Recommendation App - FINAL UI SPECIFICATION

## Overview & Context
You are tasked with redesigning and rewriting the React (Vite) frontend for a **Zomato-inspired Bento Box ML Recommendation Engine**. The core logic and API integration are fully functional, but the aesthetic execution lacks the "premium, dynamic, state-of-the-art" feel we require. 

Your objective is to deliver a flawless, pixel-perfect, highly polished Bento Box UI that perfectly executes the exact constraints and design patterns defined below.

---

## Technical Stack & Constraints
- **Framework:** React (Vite)
- **Styling:** Tailwind CSS **v4** 
  - *CRITICAL:* Do not use `tailwind.config.js`. Tailwind v4 requires all custom themes to be defined via `@theme` directives inside `index.css`.
- **Animations:** `framer-motion`
- **Icons:** `lucide-react` (NO EMOJIS ALLOWED)
- **Color Mode:** **Light Mode Only** (no dark mode overrides).

---

## Core Design Principles & Aesthetics
### 1. Typography & Colors
- **Font:** Inter or comparable modern sans-serif.
- **Color Palette (Must use exactly):**
  - **Zomato Red:** `#E23744` (Primary brand accent, CTAs, focal points).
  - **Zomato Gold:** `#F5B800` (Highlights, stars, ML tags).
  - **Zomato Charcoal:** `#1A1A1A` (Primary text, dark backgrounds for contrast panels).
  - **Zomato Lightgray:** `#F4F5F7` (App background).
- **Shadows (Bento elevations):**
  - base: `0 10px 40px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04)`
  - hover: `0 20px 50px rgba(0, 0, 0, 0.15)`
  - elevated: `0 30px 60px rgba(226, 55, 68, 0.15)` (Subtle red glow on active states).

### 2. Mobile Responsiveness (Strict Rules)
Do not take the lazy route of collapsing everything into a single vertical column on mobile. **You must maintain the Bento box aesthetic on small screens.**
1. **Keep a 2-Column Base:** Set the mobile grid to 2 columns (`grid-cols-2`).
2. **Use Asymmetrical Spanning:** Make the most important cards (like the Main Restaurant Menu or primary Zomato-red CTAs) span both columns (`col-span-2`), while keeping smaller utility cards (like persona tags, location info, stats) side-by-side in single columns (`col-span-1`).
3. **Introduce Horizontal Swiping:** For areas with multiple items (like profile chips, recommendation rails, cart items), group them into a single row with horizontal scrolling (`overflow-x-auto`, hiding the scrollbar) and `snap-x` so users can swipe left-to-right without cluttering the vertical feed.

### 3. Visual Polish
- **Food Images:** Style overhead photography (bird's eye view, 90° from above). Format them as circular plates (`rounded-full` or `border-radius: 50%`) simulating professional food photography. Float them slightly off their containers or overlap boundaries if it enhances depth.
- **Glassmorphism:** Use subtle `bg-white/80 backdrop-blur-md` and `border-white/20` for floating elements to create a sleek, premium application feel.

---

## Component Specifications (The Workflow)

### 1. Profile Selector (Top Left)
- **Content:** Pre-made personas (e.g., "Budget Explorer", "Premium Diner", "Health Conscious").
- **Interaction:** Horizontal swappable chips. Selecting one updates the active layout state.

### 2. Context Dashboard (Top Right)
- **Content:** A read-only City search bar (e.g., "Bangalore") alongside a Veg/Any diet toggle. 
- **Style:** Compact, matching the Bento elevation.

### 3. Main Menu Area (Center / Largest Span)
- **Header:** Restaurant Name ("The Spice Route"), sub-tags (North Indian, Mughlai • CP), and a distinct Green `4.3 ★` badge.
- **List Items:** Displays the fetched menu. Each row must have:
  - The circular overhead food image on the left.
  - A Zomato-style Veg (Green) / Non-Veg (Red) square-in-dot indicator.
  - Title, 2-line clamped description (`text-charcoal/60`), and Price (`₹`).
  - A prominent `+ Add` button (Red text, light red background, transitioning to solid Red on hover).

### 4. Cart & ML Recommendation Rail (Bottom Flow)
*This section dictates what happens when an item is added.*
- **Cart:** A clean summary list of active items and the Total Price.
- **Recommendation Rail:** Rendered horizontally next to or below the cart. 
  - **Header:** "PAIRS WELL WITH THIS ✦" holding an "ML GENERATED" tag.
  - **Interaction:** Horizontal scrolling (`flex-row overflow-x-auto snap-x`).
  - **Content:** 5-6 generated items. Cards must animate in gracefully (Framer Motion scale + spring).

### 5. Algorithm Insights Panel (Right Column / Floating Sidebar)
- **Trigger:** This panel *only* fades into view (opacity: 1) when the backend generates a recommendation rail, and *fades out* (opacity: 0) after 120 seconds of inactivity.
- **Aesthetic:** Dark mode styling (`bg-zomato-charcoal`) contrasting sharply with the rest of the app. Use `text-white` and `text-zomato-gold`.
- **Content:**
  - **Hexagon Candidate Shift:** A text block explaining why certain node categories (e.g., "Beverages", "Dessert") fired.
  - **LightGBM Feature Importance:** 3-4 horizontal progress bars representing parameter weights (e.g., `user_item_affinity: 87%`). The bars should fill via Framer Motion.
  - **Item2Vec Reasoning:** Monospace code blocks showing similarity scores (`similarity("Mutton Biryani", "Mint Mojito") = 0.814`).

---

## API Data Schemas
To ensure your components wire up flawlessly without crashing (No `undefined` mapping errors), map your components to exactly these structures:

**Menu Fetch:`http://localhost:8085/api/menu/{firstRestId}`**
```json
// GET /api/menu/:restaurant_id returns an array:
[
  {
    "id": 1,
    "name": "Special Cold Coffee",
    "price": 149,
    "veg": true,
    "type": "Beverage",
    "desc": "Beverage item."
  }
]
```

**Recommend Fetch:`http://localhost:8085/api/recommend`**
```json
// POST /api/recommend returns an object mapping:
{
  "success": true,
  "recommendations": [
    {
      "id": 2,
      "name": "House Tiramisu",
      "price": 279,
      "veg": true
    }
  ],
  "insights": {
    "shift": "Beverage/Extension nodes heavily activated based on cart embedding.",
    "features": [
      { "label": "user_item_affinity", "val": "87%", "w": "87%" },
      { "label": "anchor_cuisine_enc", "val": "72%", "w": "72%" }
    ]
  }
}
```

*Final Note:* Do not respond with scattered snippets. Provide a cohesive, copy-pasteable architecture of `App.jsx`, `index.css`, and the modular components inside a `src/components/` folder structure, prioritizing breathtaking UI design mechanics.
