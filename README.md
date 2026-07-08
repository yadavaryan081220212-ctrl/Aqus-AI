# aqus ai

A free, open-source personal AI assistant built with modern tools.

## Tech Stack
- **AI Models**: Ollama (local) or Google Gemini (cloud)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Database**: SQLite (chat history)
- **Web Search**: DuckDuckGo Search
- **Programming**: Python

## Setup Instructions

### Option 1: Using Ollama (Local)
1. **Install Ollama**: Download and install Ollama from https://ollama.com

2. **Pull a Model**:
   ```bash
   ollama pull qwen2.5:0.5b
   ```

3. **Configure**: In `backend/.env`, set:
   ```
   AI_PROVIDER=ollama
   AI_MODEL=qwen2.5:0.5b
   ```

### Option 2: Using Google Gemini (Cloud)
1. **Get Gemini API Key**: Get one from https://aistudio.google.com/app/apikey

2. **Configure**: In `backend/.env`, set:
   ```
   AI_PROVIDER=gemini
   AI_API_KEY=your_actual_gemini_api_key_here
   AI_MODEL=gemini-2.0-flash
   ```

### Common Steps for Both Options
3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

5. **Run the Frontend (in a new terminal)**:
   ```bash
   cd frontend
   streamlit run app.py
   ```

## Features
- 🤖 Natural conversation with Ollama or Gemini models
- 📜 Chat history stored in SQLite
- 🔍 Web search with DuckDuckGo
- 🧠 Memory toggle (remember chat history or not)
- 💬 Beautiful Streamlit UI
- 🔧 Tools to open URLs, files, and run commands

## Usage
1. Start both backend and frontend
2. Open your browser to http://localhost:8502
3. Start chatting!
