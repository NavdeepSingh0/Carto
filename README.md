<h1 align="center">Cart Super Add-On (CSAO) Rail Recommendation System</h1>
<p align="center"><i>Zomathon Hackathon Submission — Navdeep </i></p>

## Overview
This repository contains the complete end-to-end source code for the CSAO Recommendation System, tackling Zomathon Problem Statement 2.

Our solution implements a **Two-Stage Context-Aware Recommendation Engine** designed to improve Zomato's Cart-to-Order (C2O) ratio and Average Order Value (AOV). It strictly operates within a `<100ms` latency budget, acting as a real-time system to recommend highly contextual add-ons to users at the cart stage.

## Live Links & Resources
- 🌐 **Interactive Web Demo:** [https://carto-demo.netlify.app](https://carto-demo.netlify.app)
- 📊 **Kaggle Dataset:** [navdeepdhunna/csao-dataset-2](https://www.kaggle.com/datasets/navdeepdhunna/csao-dataset-2)
- 📓 **Kaggle Code:** [navdeepdhunna/carto](https://www.kaggle.com/code/navdeepdhunna/carto)
- 📄 **Documentation:** See `docs/csao_solution_final.docx` for the comprehensive mathematical breakdown.

## Repository Structure

```text
├── bento_demo/                 # The interactive proof-of-concept application
│   ├── backend/                # FastAPI serving layer for <100ms ML inference
│   └── frontend/               # React (Vite) user interface
├── datasets/                   # Synthetic relational data (users, restaurants, orders)
├── docs/                       # Solution documentation, SVGs, and engineering notes
├── model_artifacts/            # Pre-trained models (LightGBM ranker + Item2Vec)
└── training_scripts/           # The core Machine Learning pipeline
    ├── generate_csao_data.py   # Synthetic data generator + Hexagon candidate generation
    ├── train_lightgbm.py       # Stage 2 ranker training + Isotonic Calibration
    └── train_and_export.py     # End-to-end pipeline runner
```

## System Architecture Highlights
1. **Stage 1: The Hexagon Candidate Engine** - Generates a targeted pool of ~50-100 candidates based on culinary rules (Extension, Texture, Co-Occurrence, Time-of-Day Beverage, Regional Dessert, Budget/Habit).
2. **Feature Engineering** - `Item2Vec` embeddings handle new item sparsity. `Cold` features run nightly; `Hot` features (cart variance, price ratio) compute per request.
3. **Stage 2: LightGBM Ranker** - Ranks the candidate pool via Gradient Boosted Trees.
4. **Isotonic Calibration & Hard Constraints** - Ensures strict adherence to Veg/Non-Veg rules and prevents conflicting cuisine pairings. Output scores are true probabilistic likelihoods of user acceptance.

## Running Locally

To run the interactive demonstration server locally:

### Terminal 1 (FastAPI Backend)
```bash
cd bento_demo/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8085 --reload
```

### Terminal 2 (React Frontend)
```bash
cd bento_demo/frontend
npm install
npm run dev
```

Visit `http://localhost:5174` in your browser.
