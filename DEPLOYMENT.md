# Deployment Guide for aqus ai

## Overview
- **Frontend**: Next.js (Vercel)
- **Backend**: FastAPI (Render)
- **AI**: Google Gemini API

---

## 1. Backend Deployment (Render)

### Step 1: Prepare Backend
1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repo

### Step 2: Configure Render
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `python backend/main.py`
- **Health Check Path**: `/api/health`
- **Environment Variables**:
  - `AI_PROVIDER`: `gemini`
  - `AI_API_KEY`: Your Gemini API key
  - `AI_MODEL`: `gemini-3-flash-preview`
  - `ENABLE_LOCAL_TOOLS`: `false`
  - `CORS_ORIGINS`: Your frontend URL (e.g., `https://your-app.vercel.app`)
  - `HOST`: `0.0.0.0`
  - `PORT`: Leave unset and let Render provide it automatically

---

## 2. Frontend Deployment (Vercel)

### Step 1: Prepare Frontend
1. Push your code to GitHub
2. Import the project on Vercel
3. Make sure the **Root Directory** is set to `frontend-next`

### Step 2: Configure Vercel
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: Your Render backend URL (e.g., `https://your-backend.onrender.com`)

---

## Local Development

### Run Backend
```bash
pip install -r backend/requirements.txt
python main.py
```

### Run Frontend
```bash
cd frontend-next
npm install
npm run dev
```

## Notes
- Server-side desktop actions like opening apps, files, or local browser tabs are disabled by default for hosted deployments.
- Keep `backend/.env` and `frontend-next/.env.local` out of version control and set production values in Render/Vercel dashboards.
