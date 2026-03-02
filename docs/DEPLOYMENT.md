# 🚀 CSAO Demo — Deployment Guide

## Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial: CSAO demo"
# Create a new repo on GitHub called 'Zomathon' (public or private)
git remote add origin https://github.com/YOUR-USERNAME/Zomathon.git
git push -u origin main
```

## Step 2: Deploy the Backend on Render.com (free)

1. Go to [render.com](https://render.com) → Sign up with GitHub
2. Click **New → Web Service**
3. Connect your **Zomathon** GitHub repo
4. Configure:
   - **Name:** `csao-backend`
   - **Root Directory:** `bento_demo/backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**
6. Wait ~3 min. Your backend URL will be: `https://csao-backend.onrender.com`

> ⚠️ **Note on free tier:** Render free services spin down after 15 min of inactivity and take ~30s to wake on the next request. For a hackathon demo this is fine.

## Step 3: Deploy the Frontend on Netlify (free)

1. Update `bento_demo/frontend/.env.production`:
   ```
   VITE_API_BASE=https://csao-backend.onrender.com
   ```
   (Replace with your actual Render backend URL)

2. Go to [netlify.com](https://netlify.com) → Sign up with GitHub
3. Click **Add new site → Import an existing project**
4. Connect GitHub → select **Zomathon**
5. Configure:
   - **Base directory:** `bento_demo/frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `bento_demo/frontend/dist`
6. Click **Deploy site**
7. Your frontend URL will be: `https://csao-demo.netlify.app`

## Step 4: Update Documents with Live Links

Once deployed, update these three places:

### In `csao_solution_document.md` Section 12:
| Resource | Live Link |
|---|---|
| Dataset | https://kaggle.com/datasets/navdeepdhunna/csao-dataset-2 |
| Kaggle Notebook | [Add your notebook URL after publishing] |
| Interactive Demo | https://csao-demo.netlify.app |

### In `csao_solution_final.docx`:
Run the regeneration script to embed the URLs.

## Architecture (Deployed)

```
User Browser
    │
    ▼
Netlify CDN (React frontend)
    │  HTTPS API calls
    ▼
Render.com Web Service (FastAPI)
    │  Loads from disk at startup:
    ├─ datasets/   (CSV files)
    └─ model_artifacts/ (LightGBM + Item2Vec)
```
