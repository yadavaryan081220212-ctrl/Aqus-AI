# Deployment Guide for aqus ai

## Overview
- **Frontend**: Next.js (Vercel)
- **Backend**: FastAPI (Render)
- **AI**: Ollama (local) or cloud providers (Gemini, Groq, OpenRouter, etc.)

---

## 1. Backend Deployment (Render)

### Step 1: Prepare Backend
1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repo

### Step 2: Configure Render
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `cd backend && python main.py`
- **Environment Variables**:
  - `AI_PROVIDER`: `ollama` (or your cloud provider)
  - `AI_API_KEY`: (if using cloud provider)
  - `AI_MODEL`: `qwen2.5:0.5b` (or your model)
  - `CORS_ORIGINS`: Your frontend URL (e.g., `https://your-app.vercel.app`)
  - `HOST`: `0.0.0.0`
  - `PORT`: `10000` (Render's default)

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
cd backend
pip install -r requirements.txt
python main.py
```

### Run Frontend
```bash
cd frontend-next
npm install
npm run dev
```
