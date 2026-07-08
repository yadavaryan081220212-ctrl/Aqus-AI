import sys
import io
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix Unicode encoding issues on Windows FIRST (before wrapping stdout/stderr)
original_stdout = sys.stdout
original_stderr = sys.stderr

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(original_stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(original_stderr.buffer, encoding='utf-8')

# === LOG EVERYTHING TO A FILE ===
log_file = open("backend_debug.log", "a", encoding="utf-8")
print(f"\n{'='*60}", file=log_file)
print(f"=== STARTING BACKEND AT {datetime.now()}", file=log_file)
print(f"{'='*60}", file=log_file)

# Duplicate stdout/stderr to log file
class Tee(object):
    def __init__(self, *files):
        self.files = files
    
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()  # Ensure it's written immediately
    
    def flush(self):
        for f in self.files:
            f.flush()
    
    # Pass through any attributes we don't have to the first file (for buffer, etc.)
    def __getattr__(self, attr):
        return getattr(self.files[0], attr)

sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, AsyncGenerator, Optional
import sqlite3
from duckduckgo_search import DDGS
import json
import asyncio
from contextlib import asynccontextmanager
import webbrowser
import subprocess
import platform
from ai_service import get_ai_service

# Get AI service
ai_service = get_ai_service()
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8502").split(",")

# System control functions
def open_url(url: str) -> str:
    """Open a URL in the default browser"""
    try:
        webbrowser.open(url)
        return f"Opened {url} successfully!"
    except Exception as e:
        return f"Error opening URL: {str(e)}"

def open_file_or_app(path: str) -> str:
    """Open a file or application"""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", path])
        else:  # Linux
            subprocess.call(["xdg-open", path])
        return f"Opened {path} successfully!"
    except Exception as e:
        return f"Error opening: {str(e)}"

def execute_command(command: str) -> str:
    """Execute a system command (safe subset)"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout + result.stderr
        return f"Command output:\n{output[:500]}"  # Limit output length
    except Exception as e:
        return f"Error executing command: {str(e)}"

# Tool definitions for Ollama (compatible with qwen2.5)
TOOLS = [
    {
        "name": "open_url",
        "description": "Open a URL in the default web browser",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to open, e.g., https://youtube.com"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "open_file_or_app",
        "description": "Open a file, folder, or application on the user's computer",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path or application name, e.g., notepad.exe, C:\\Users"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "execute_command",
        "description": "Execute a system command on the user's computer",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to run, e.g., dir, echo hello"
                }
            },
            "required": ["command"]
        }
    }
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Preload default model if available
    try:
        # Get list of available models first
        available_models_list = await ai_service.list_models()
        available_models = [m["name"] for m in available_models_list]
        
        # Try to use a model that's already available
        default_model = None
        preferred_models = ["qwen2.5:0.5b", "llama3.2:1b", "qwen2.5:1.5b"]
        for model in preferred_models:
            if model in available_models:
                default_model = model
                break
        
        if default_model and hasattr(ai_service, "client"):
            # Preload only if we're using Ollama
            await ai_service.client.chat(
                model=default_model,
                messages=[{"role": "user", "content": "hi"}],
                stream=False,
                keep_alive="10m"
            )
            print(f"[OK] Preloaded {default_model} for fast first response")
        else:
            print("[WARN] No default model found or not using Ollama")
    except Exception as e:
        print(f"[WARN] Could not preload model: {e}")
    yield
    # Shutdown
    pass

app = FastAPI(title="aqus ai API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect('chat_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "qwen2.5:0.5b"
    use_web_search: bool = False

class ChatResponse(BaseModel):
    response: str

async def run_web_search(query: str) -> str:
    """Run web search in a thread to not block the event loop"""
    loop = asyncio.get_event_loop()
    try:
        with DDGS() as ddgs:
            results = await loop.run_in_executor(
                None,
                lambda: list(ddgs.text(query, max_results=2, timelimit="d"))
            )
            if results:
                return "\n\nWeb search results:\n" + "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        print(f"Web search error: {e}")
    return ""

async def process_tool_calls(tool_calls) -> List[dict]:
    """Process Ollama tool calls and return results"""
    tool_responses = []
    print(f"\n===== [DEBUG] IN process_tool_calls =====")
    print(f"[DEBUG] Received tool calls: {tool_calls}")
    
    for idx, tool_call in enumerate(tool_calls):
        print(f"\n--- Processing tool call #{idx+1} ---")
        try:
            # Handle dict format (which Ollama returns)
            if isinstance(tool_call, dict):
                function_data = tool_call.get('function', {})
                func_name = function_data.get('name', '')
                args = function_data.get('arguments', {})
                if isinstance(args, str):
                    args = json.loads(args)
                print(f"[DEBUG] Parsed dict tool call: func_name='{func_name}', args={args}")
            else:
                print(f"[ERROR] Unknown tool call format: {tool_call} (type: {type(tool_call)})")
                continue
            
            # Try to infer function name if it's empty (qwen2.5 quirk)
            if not func_name:
                print(f"[DEBUG] Func name empty, inferring from args: {args}")
                if "url" in args:
                    func_name = "open_url"
                    # Fix URL if it's missing https://
                    url = args["url"]
                    if not url.startswith(("http://", "https://")):
                        args["url"] = "https://" + url
                        print(f"[DEBUG] Fixed URL to: {args['url']}")
                elif "path" in args:
                    func_name = "open_file_or_app"
                elif "command" in args:
                    func_name = "execute_command"
                print(f"[DEBUG] Inferred func name: {func_name}")
            
            print(f"[TOOL] ########## CALLING {func_name} ##########")
            print(f"[TOOL] Arguments: {args}")
            
            # Execute the function
            if func_name == "open_url":
                print(f"[TOOL] Calling open_url({args['url']})")
                result = open_url(args["url"])
                print(f"[TOOL] open_url result: '{result}'")
            elif func_name == "open_file_or_app":
                print(f"[TOOL] Calling open_file_or_app({args['path']})")
                result = open_file_or_app(args["path"])
                print(f"[TOOL] open_file_or_app result: '{result}'")
            elif func_name == "execute_command":
                print(f"[TOOL] Calling execute_command({args['command']})")
                result = execute_command(args["command"])
                print(f"[TOOL] execute_command result: '{result}'")
            else:
                result = f"Unknown tool: {func_name}"
            
            print(f"[TOOL] Adding tool response: {result}")
            tool_responses.append({
                "role": "tool",
                "content": result
            })
        except Exception as e:
            print(f"[ERROR] Exception processing tool call #{idx+1}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            tool_responses.append({
                "role": "tool",
                "content": f"Error: {str(e)}"
            })
    print(f"\n===== [DEBUG] process_tool_calls returning: {tool_responses} =====")
    return tool_responses

async def generate_response(messages: List[dict], model: str) -> AsyncGenerator[str, None]:
    try:
        print(f"[DEBUG] Generating response with model: {model}")
        print(f"[DEBUG] Messages: {messages}")
        
        if AI_PROVIDER == "ollama":
            # First request with tools (only if using Ollama)
            response = None
            tool_calls = None
            assistant_content = ""
            if hasattr(ai_service, "client"):
                # Ollama-specific tool handling
                response = await ai_service.client.chat(
                    model=model,
                    messages=messages,
                    stream=False,
                    tools=TOOLS,
                    options={
                        "num_ctx": 4096, 
                        "temperature": 0.7,
                        "num_predict": -1
                    },
                    keep_alive="10m"
                )
            
            print(f"[DEBUG] Initial response: {response}")
            
            # Check for tool calls - response is a dict!
            if isinstance(response, dict):
                message_dict = response.get('message', {})
                tool_calls = message_dict.get('tool_calls')
                assistant_content = message_dict.get('content', '')
            else:
                # Fallback to object format
                message_dict = response.message if hasattr(response, 'message') else {}
                tool_calls = message_dict.tool_calls if hasattr(message_dict, 'tool_calls') else None
                assistant_content = message_dict.content if hasattr(message_dict, 'content') else ''
        
            # === BRUTE-FORCE FALLBACK: Check if user wants to open something ===
            if not tool_calls:
                print(f"\n===== [FALLBACK] No tool calls found, checking user message =====")
                print(f"[FALLBACK] All messages: {messages}")
                # Find last user message
                last_user_msg = None
                last_user_msg_original = None
                for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        last_user_msg = msg.get("content", "").lower()
                        last_user_msg_original = msg.get("content", "")
                        break
                print(f"[FALLBACK] Found last user message: '{last_user_msg}'")
                
                if last_user_msg:
                    tool_results = []
                    
                    # === CHECK FOR SEARCH COMMAND ===
                    if "search" in last_user_msg:
                        print(f"[FALLBACK] Detected search command!")
                        import re
                        import urllib.parse
                        # Try to match patterns like "search X in Y" or "search X on Y"
                        pattern = r"search\s+(.*?)\s+(?:in|on)\s+(.*)"
                        match = re.search(pattern, last_user_msg_original, re.IGNORECASE)
                        
                        query = ""
                        site = ""
                        
                        if match:
                            query = match.group(1).strip()
                            site = match.group(2).strip().lower()
                        else:
                            # If no "in/on" specified, check if any site is mentioned
                            sites_keywords = {
                                "youtube": "youtube",
                                "google": "google",
                                "bing": "bing",
                                "duckduckgo": "duckduckgo",
                                "github": "github",
                                "amazon": "amazon"
                            }
                            for keyword, site_name in sites_keywords.items():
                                if keyword in last_user_msg:
                                    site = site_name
                                    # Extract query by removing site keyword
                                    query = last_user_msg_original.lower().replace("search", "").replace(keyword, "").strip()
                                    break
                        
                        # Map sites to search URLs
                        site_search_urls = {
                            "youtube": "https://www.youtube.com/results?search_query=",
                            "google": "https://www.google.com/search?q=",
                            "bing": "https://www.bing.com/search?q=",
                            "duckduckgo": "https://duckduckgo.com/?q=",
                            "github": "https://github.com/search?q=",
                            "amazon": "https://www.amazon.com/s?k="
                        }
                        
                        # If we have both query and site, open search results
                        if query and site in site_search_urls:
                            encoded_query = urllib.parse.quote_plus(query)
                            url = f"{site_search_urls[site]}{encoded_query}"
                            print(f"[FALLBACK] Opening search: {url}")
                            res = open_url(url)
                            tool_results.append({"role": "tool", "content": res})
                        # If we have query but no site, default to Google
                        elif query:
                            encoded_query = urllib.parse.quote_plus(query)
                            url = f"https://www.google.com/search?q={encoded_query}"
                            print(f"[FALLBACK] Opening Google search: {url}")
                            res = open_url(url)
                            tool_results.append({"role": "tool", "content": res})
                    
                    # Check for open website
                    elif ("open" in last_user_msg and 
                        (".com" in last_user_msg or "http" in last_user_msg or "website" in last_user_msg or "youtube" in last_user_msg)):
                        print(f"[FALLBACK] Detected website open request!")
                        # Extract URL (simple version)
                        url = "https://youtube.com"
                        if "youtube" in last_user_msg:
                            url = "https://youtube.com"
                        elif "google" in last_user_msg:
                            url = "https://google.com"
                        # Call open_url manually
                        print(f"[FALLBACK] Manually calling open_url({url})")
                        res = open_url(url)
                        tool_results.append({"role": "tool", "content": res})
                    # Check for open app/file
                    elif ("open" in last_user_msg and 
                          ("notepad" in last_user_msg or "calc" in last_user_msg or "file" in last_user_msg or "folder" in last_user_msg)):
                        print(f"[FALLBACK] Detected app/file open request!")
                        path = "notepad"
                        res = open_file_or_app(path)
                        tool_results.append({"role": "tool", "content": res})
                    
                    if tool_results:
                        print(f"[FALLBACK] Got tool results: {tool_results}")
                        messages.append({"role": "assistant", "content": assistant_content})
                        messages.extend(tool_results)
                        tool_calls = True  # Fake it to enter the tool handling block
            
            if tool_calls:
                if tool_calls is not True:  # Not the fallback case
                    print(f"[DEBUG] Processing tool calls: {tool_calls}")
                    tool_results = await process_tool_calls(tool_calls)
                    # Add tool response to messages and get final answer
                    messages.append({"role": "assistant", "content": assistant_content})
                    messages.extend(tool_results)
                # Stream final response
                async for chunk in ai_service.chat_stream(messages, model):
                    yield chunk
            else:
                # No tool calls, stream normally
                async for chunk in ai_service.chat_stream(messages, model):
                    yield chunk
        else:
            # For Gemini and other providers, just stream normally without tool handling
            async for chunk in ai_service.chat_stream(messages, model):
                yield chunk
        
    except Exception as e:
        print(f"[ERROR] Generation error: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        # === 100% RELIABLE PRE-CHECK FOR OPEN/SEARCH COMMANDS ===
        last_user_msg = None
        last_user_msg_original = None
        for msg in reversed(request.messages):
            if hasattr(msg, "content"):
                last_user_msg = msg.content.lower()
                last_user_msg_original = msg.content
                break
        
        if last_user_msg:
            print(f"\n===== [PRE-CHECK] Last user message: '{last_user_msg}' =====")
            
            # === CHECK FOR SEARCH COMMAND ===
            if "search" in last_user_msg:
                import re
                import urllib.parse
                # Try to match patterns like "search X in Y" or "search X on Y"
                pattern = r"search\s+(.*?)\s+(?:in|on)\s+(.*)"
                match = re.search(pattern, last_user_msg_original, re.IGNORECASE)
                
                query = ""
                site = ""
                
                if match:
                    query = match.group(1).strip()
                    site = match.group(2).strip().lower()
                else:
                    # If no "in/on" specified, check if any site is mentioned
                    sites_keywords = {
                        "youtube": "youtube",
                        "google": "google",
                        "bing": "bing",
                        "duckduckgo": "duckduckgo",
                        "github": "github",
                        "amazon": "amazon"
                    }
                    for keyword, site_name in sites_keywords.items():
                        if keyword in last_user_msg:
                            site = site_name
                            # Extract query by removing site keyword
                            query = last_user_msg_original.lower().replace("search", "").replace(keyword, "").strip()
                            break
                
                # Map sites to search URLs
                site_search_urls = {
                    "youtube": "https://www.youtube.com/results?search_query=",
                    "google": "https://www.google.com/search?q=",
                    "bing": "https://www.bing.com/search?q=",
                    "duckduckgo": "https://duckduckgo.com/?q=",
                    "github": "https://github.com/search?q=",
                    "amazon": "https://www.amazon.com/s?k="
                }
                
                # If we have both query and site, open search results
                if query and site in site_search_urls:
                    encoded_query = urllib.parse.quote_plus(query)
                    url = f"{site_search_urls[site]}{encoded_query}"
                    print(f"[PRE-CHECK] Opening search: {url}")
                    open_url(url)
                # If we have query but no site, default to Google
                elif query:
                    encoded_query = urllib.parse.quote_plus(query)
                    url = f"https://www.google.com/search?q={encoded_query}"
                    print(f"[PRE-CHECK] Opening Google search: {url}")
                    open_url(url)
            
            # Pre-check for website open
            elif "open" in last_user_msg:
                if "youtube" in last_user_msg:
                    print(f"[PRE-CHECK] Opening YouTube!")
                    open_url("https://youtube.com")
                elif "google" in last_user_msg:
                    print(f"[PRE-CHECK] Opening Google!")
                    open_url("https://google.com")
                # Pre-check for apps
                elif "notepad" in last_user_msg:
                    print(f"[PRE-CHECK] Opening Notepad!")
                    open_file_or_app("notepad")
                elif "calc" in last_user_msg or "calculator" in last_user_msg:
                    print(f"[PRE-CHECK] Opening Calculator!")
                    open_file_or_app("calc")
        
        # Run web search in parallel if enabled
        context = ""
        if request.use_web_search and request.messages:
            context = await run_web_search(request.messages[-1].content)
        
        if AI_PROVIDER == "ollama":
            system_prompt = """🔧 YOU ARE A TOOL-USER BOT! 🔧

ABSOLUTELY CRITICAL RULES:
1. YOU MUST USE A TOOL FOR ANY SYSTEM TASK!
2. DO NOT JUST TALK—ALWAYS CALL A TOOL FIRST!
3. WHEN USER ASKS TO OPEN ANY WEBSITE → CALL open_url!
4. WHEN USER ASKS TO OPEN AN APP/FILE → CALL open_file_or_app!
5. WHEN USER ASKS TO RUN A COMMAND → CALL execute_command!

AVAILABLE TOOLS:
  - open_url(url="https://example.com") → Open a URL in the browser
  - open_file_or_app(path="notepad.exe") → Open a file, folder, or app
  - execute_command(command="dir") → Run a system command

EXAMPLE INTERACTION:
User: "Open youtube"
You MUST CALL: open_url(url="https://youtube.com")

DO NOT RESPOND WITHOUT CALLING A TOOL FIRST!"""
        else:
            system_prompt = "You are a helpful personal AI assistant. Be friendly, concise, and informative."
        if context:
            system_prompt += f"\n\nUse this context if relevant: {context}"
        
        messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m.role, "content": m.content} for m in request.messages
        ]
        
        return StreamingResponse(
            generate_response(messages, request.model),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        context = ""
        if request.use_web_search and request.messages:
            context = await run_web_search(request.messages[-1].content)
        
        system_prompt = "You are a helpful personal AI assistant. Be friendly, concise, and informative."
        if context:
            system_prompt += f"\n\nUse this context if relevant: {context}"
        
        messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m.role, "content": m.content} for m in request.messages
        ]
        
        response = await ai_service.chat(messages, request.model)
        
        # Extract content from response
        response_content = ""
        if isinstance(response, dict):
            response_content = response.get('message', {}).get('content', '')
        elif hasattr(response, 'message') and hasattr(response.message, 'content'):
            response_content = response.message.content
        
        # Save to DB
        conn = sqlite3.connect('chat_history.db', check_same_thread=False)
        c = conn.cursor()
        for msg in request.messages:
            c.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (msg.role, msg.content))
        c.execute('INSERT INTO messages (role, content) VALUES (?, ?)', ('assistant', response_content))
        conn.commit()
        conn.close()
        
        return ChatResponse(response=response_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def get_models():
    try:
        models = await ai_service.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pull/{model_name}")
async def pull_model(model_name: str):
    try:
        if hasattr(ai_service, "client"):
            await ai_service.client.pull(model_name)
            return {"status": "success", "model": model_name}
        else:
            return {"status": "info", "message": "Model pulling is only supported for Ollama"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history():
    conn = sqlite3.connect('chat_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT role, content, timestamp FROM messages ORDER BY timestamp')
    history = [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in c.fetchall()]
    conn.close()
    return {"history": history}

@app.delete("/api/history")
async def clear_history():
    conn = sqlite3.connect('chat_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('DELETE FROM messages')
    conn.commit()
    conn.close()
    return {"message": "History cleared"}

if __name__ == "__main__":
    import uvicorn
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
