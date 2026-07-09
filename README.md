# aqus ai

A free, open-source personal AI assistant built with modern tools.

## Tech Stack
- **AI Models**: Google Gemini API by default, with optional local Ollama support
- **Backend**: FastAPI
- **Frontend**: Next.js
- **Database**: SQLite (chat history)
- **Web Search**: DuckDuckGo Search
- **Programming**: Python and TypeScript

## Setup Instructions

### Option 1: Google Gemini API
1. **Get a Gemini API key** from https://aistudio.google.com/app/apikey
2. **Configure** `backend/.env`:
   ```
   AI_PROVIDER=gemini
   AI_API_KEY=your_actual_gemini_api_key_here
   AI_MODEL=gemini-3-flash-preview
   ENABLE_LOCAL_TOOLS=false
   ```

### Option 2: Ollama (Local Only)
1. **Install Ollama** from https://ollama.com
2. **Pull a model**:
   ```bash
   ollama pull qwen2.5:0.5b
   ```
3. **Configure** `backend/.env`:
   ```
   AI_PROVIDER=ollama
   AI_MODEL=qwen2.5:0.5b
   ENABLE_LOCAL_TOOLS=true
   ```

### Run Locally
1. **Install backend dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Run the backend**:
   ```bash
   cd backend
   python main.py
   ```

3. **Run the frontend** in a new terminal:
   ```bash
   cd frontend-next
   npm install
   npm run dev
   ```

## Features
- 🤖 Natural conversation with Gemini or Ollama models
- 📜 Chat history stored in SQLite
- 🔍 Web search with DuckDuckGo
- 🧠 Memory toggle (remember chat history or not)
- 💬 Next.js chat interface
- 🔧 Optional local tools for desktop-only Ollama sessions

## Usage
1. Start both backend and frontend
2. Open your browser to http://localhost:3000
3. Start chatting!
