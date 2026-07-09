import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Personal AI Assistant", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Caching for API base
@st.cache_data
def get_api_base():
    return "http://localhost:8000"

API_BASE = get_api_base()

st.title("🤖 aqus ai")
st.markdown("Your free, private AI companion - optimized for speed!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Fetch available models from backend
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_available_models():
    try:
        response = requests.get(f"{API_BASE}/api/models")
        response.raise_for_status()
        data = response.json()
        models = [m["name"] for m in data.get("models", []) if m["name"] != "llama3:latest"]
        # Add friendly descriptions for known models
        model_descriptions = {
            "qwen2.5:0.5b": "Tiny (~390 MB) - Fastest!",
            "llama3.2:1b": "Small (~1.3 GB) - Fast & Good",
            "qwen2.5:1.5b": "Small (~950 MB) - Balanced",
            "llama3.2:3b": "Medium (~2.0 GB) - Better Quality",
            "phi3:mini": "Small (~2.3 GB) - Good for coding",
            "models/gemini-3-flash-preview": "Gemini 3 Flash - Preview",
            "models/gemini-1.5-flash": "Gemini 1.5 Flash - Fast",
            "models/gemini-1.5-pro": "Gemini 1.5 Pro - High Quality",
            "gemini-3-flash-preview": "Gemini 3 Flash - Preview",
            "gemini-1.5-flash": "Gemini 1.5 Flash - Fast",
            "gemini-1.5-pro": "Gemini 1.5 Pro - High Quality"
        }
        # Return models with descriptions if available
        available_models = {}
        for m in models:
            available_models[m] = model_descriptions.get(m, m)
        return available_models
    except Exception as e:
        st.warning(f"Could not fetch models: {e}")
        # Fallback to default models
        return {"qwen2.5:0.5b": "Tiny (~390 MB) - Fastest!"}

# Sidebar
with st.sidebar:
    st.subheader("⚙️ Settings")
    
    # Model selection
    available_models = get_available_models()
    model_options_list = list(available_models.keys())
    
    if model_options_list:
        model = st.selectbox(
            "Model",
            model_options_list,
            index=0,
            format_func=lambda x: f"{x} ({available_models[x]})"
        )
    else:
        st.error("No models available! Please pull a model first.")
        model = "qwen2.5:0.5b"
    
    use_web_search = st.checkbox("Enable Web Search (slower)", value=False)
    use_memory = st.checkbox("Enable Memory (remember chat history)", value=True)
    
    st.divider()
    
    st.subheader("🛠️ Tools")
    
    if st.button("Clear Chat History", use_container_width=True):
        try:
            requests.delete(f"{API_BASE}/api/history")
            st.session_state.messages = []
            st.success("✅ History cleared!")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()
    
    st.subheader("📥 Quick Setup")
    st.info("Pull small models for faster responses:")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Pull qwen2.5:0.5b", type="primary", use_container_width=True):
            with st.spinner("Pulling model..."):
                try:
                    requests.post(f"{API_BASE}/api/pull/qwen2.5:0.5b")
                    st.success("✅ Model pulled!")
                except Exception as e:
                    st.error(f"Error: {e}")
    with col_b:
        if st.button("Pull llama3.2:1b", use_container_width=True):
            with st.spinner("Pulling model..."):
                try:
                    requests.post(f"{API_BASE}/api/pull/llama3.2:1b")
                    st.success("✅ Model pulled!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.divider()
    st.info("💡 Tips:\n1. Use qwen2.5:0.5b (Ollama) or Gemini 3 Flash for speed\n2. Backend supports both Ollama and Gemini\n3. Keep web search off for speed")

# Chat area
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("What's on your mind?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            if use_memory:
                # Send full chat history
                payload = {
                    "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    "model": model,
                    "use_web_search": use_web_search
                }
            else:
                # Only send the current user message
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "model": model,
                    "use_web_search": use_web_search
                }
            
            # Debug: print what we're sending
            print(f"[DEBUG] Sending payload with {len(payload['messages'])} messages, use_memory={use_memory}")
            print(f"[DEBUG] Messages: {payload['messages']}")
            
            # Optimized streaming without sseclient (faster)
            response = requests.post(
                f"{API_BASE}/api/chat/stream",
                json=payload,
                stream=True,
                headers={"Accept": "text/event-stream"},
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            
            # Process stream directly for speed
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "content" in data:
                            full_response += data["content"]
                            message_placeholder.markdown(full_response + "▌")
                        elif "error" in data:
                            st.error(f"❌ Error: {data['error']}")
                            st.info("💡 Make sure backend is running on port 8000!")
                            break
                    except json.JSONDecodeError:
                        continue
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection Error!")
            st.info("💡 Make sure backend is running on port 8000!")
        except Exception as e:
            st.error(f"❌ Error: {e}")
