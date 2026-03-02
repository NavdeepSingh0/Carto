# Zomathon Project: Context & Handoff Document

## 1. High-Level Project Objective
The goal is to architect and implement a "Mobile App Architecture Modernization" for a food recommendation platform. The app is a mobile-first web application designed to mimic a native, premium, cinematic mobile app experience. 

**Key Features:**
*   A decoupled **FastAPI backend** serving ML recommendations.
*   A highly experiential **frontend** (originally Vanilla JS + GSAP, now migrating to React/Vite "Bento" architecture) with cinematic animations and a premium UI.
*   AI-generated food imagery for recommendations.
*   A detailed, glassmorphism-styled "explain panel" that breaks down the ML recommendation logic (Confidence score, Item2Vec similarity, Budget fit, etc.).

## 2. Iteration 1: Vanilla JS + GSAP Architecture (`modern_csao/`)
We initially built the application using a pure Vanilla JS frontend with GSAP for complex view transitions, talking to a Python/FastAPI backend.

### The Debugging Journey & Solutions (What we just fixed)
We encountered a major blocking issue where clicking a profile card on the initial screen resulted in no navigation ("we don't go nowhere"). Here is the step-by-step diagnostic and solution path we took:

#### A. The "Fake" CORS Issue
*   **Symptom**: The browser console showed CORS blocking the request to `/api/restaurants`. Navigating failed silently.
*   **Diagnosis**: We tested the backend directly and realized the CORS headers were configured correctly. However, a request to `/api/restaurants` was throwing a **500 Internal Server Error**. Because FastAPI does not append CORS headers to unhandled 500 exceptions, the browser interpreted it as a CORS violation.

#### B. Fixing the Backend ML Data Integration
*   **Symptom**: The `500 Error` on `/api/restaurants`.
*   **Diagnosis**: The python code was trying to parse the ML Engine's `restaurants.csv` incorrectly.
*   **Fixes Implemented**:
    1.  **Column Mismatch**: Changed `r["restaurant_name"]` to `r["name"]` to match the CSV structure.
    2.  **Type Mismatch**: The code treated `price_range` as an integer multiplier, but the CSV contained strings (`"budget"`, `"mid"`, `"premium"`). We mapped these strings to display values (`"₹"`, `"₹₹"`) and numeric cost multipliers.
    3.  **Filtering Logic**: We added the missing logic to actually filter the returned `raw_rests` dataframe by the requested `city`.

#### C. Fixing GSAP Animation & CSS View Visibility
*   **Symptom**: After the backend returned a successful 200 OK, the navigation fired, but the screen became completely blank. The DOM contained the restaurant elements, but they weren't visible.
*   **Fix 1 (CSS Prioritization)**: the `.hidden` utility class had `display: none !important;`. When GSAP tried to animate the view in using inline `display: flex`, CSS `!important` overruled it. We removed `!important`.
*   **Fix 2 (GSAP Sequencing)**: Even when visible, the restaurant list was pushed down ~400px below the viewport. We fixed `animations.js` because child elements (`[data-animate]`) were being animated *before* the parent view was fully displayed or they were on unchained timelines. We changed `gsap.from()` to `tl.from()` and synced the sequence.

#### D. Interactive UI Toggles
*   **Symptom**: Clicking city filters ("Mumbai", "Delhi") didn't update the UI state.
*   **Fix**: Added Javascript DOM manipulation to remove and re-apply the `.active` class to the city pills in `app.js`.

---

## 3. Current State & Shift to Iteration 2: "Bento" Architecture
Based on the current workspace, the project is undergoing a massive UI/UX refactor moving away from the Vanilla/GSAP `modern_csao` directory to a new React-based architecture in the `bento_demo/` directory.

**Current Tech Stack (Iteration 2):**
*   **Frontend**: React + Vite (running on port 8083/8084), utilizing a Bento-box style UI layout component structure (`BentoCard.jsx`, `CitySearchAndDiet.jsx`, `ProfileSelector.jsx`).
*   **Backend**: Python FastAPI via Uvicorn (running on port 8085).

## 4. Notes for the Next Agent
1.  **Backend Parity**: Ensure the new Bento frontend properly communicates with the endpoints on the new backend running on 8085. Ensure it expects the string-based `price_range` ("budget", "mid") we fixed in iteration 1.
2.  **Animation Migration**: The user highly values a premium, cinematic feel. Translating the complex GSAP timelines from `animations.js` (like the sliding hero card and dynamic confidence bars) into Framer Motion or React-Spring for the new Bento UI will be critical.
3.  **Data Flow**: The core flow remains: `Select Profile -> Select City -> View Restaurants -> View Menu/Cart -> Trigger ML Recommendation -> View Explain Panel`. Ensure the new React components share state (likely via Context API or Zustand) to pass the `cart` and `profile_id` seamlessly to the recommendation endpoint.
