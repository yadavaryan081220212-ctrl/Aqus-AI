import os
import json
from pathlib import Path
from typing import List, AsyncGenerator
from dotenv import load_dotenv

# Load environment variables from correct path
project_root = Path(__file__).parent.parent
load_dotenv(dotenv_path=project_root / "backend" / ".env")

# Load AI provider from env
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-3-flash-preview")

class AIService:
    """Abstract base class for AI providers"""
    async def chat_stream(
        self,
        messages: List[dict],
        model: str,
        tools: List[dict] = None
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError

    async def chat(
        self,
        messages: List[dict],
        model: str,
        tools: List[dict] = None
    ) -> dict:
        raise NotImplementedError

    async def list_models(self) -> List[dict]:
        raise NotImplementedError

class OllamaService(AIService):
    def __init__(self):
        import ollama
        self.client = ollama.AsyncClient()
    
    async def chat_stream(
        self,
        messages: List[dict],
        model: str,
        tools: List[dict] = None
    ) -> AsyncGenerator[str, None]:
        import ollama
        stream = await self.client.chat(
            model=model,
            messages=messages,
            stream=True,
            tools=tools,
            options={
                "num_ctx": 4096, 
                "temperature": 0.7,
                "num_predict": -1
            },
            keep_alive="10m"
        )
        
        async for chunk in stream:
            chunk_dict = chunk if isinstance(chunk, dict) else chunk.__dict__
            msg = chunk_dict.get("message", {})
            if isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                content = msg.content if hasattr(msg, "content") else ""
            if content:
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    async def chat(
        self,
        messages: List[dict],
        model: str,
        tools: List[dict] = None
    ) -> dict:
        response = await self.client.chat(
            model=model,
            messages=messages,
            stream=False,
            tools=tools,
            options={
                "num_ctx": 4096, 
                "temperature": 0.7,
                "num_predict": -1
            },
            keep_alive="10m"
        )
        return response

    async def list_models(self) -> List[dict]:
        models_response = await self.client.list()
        return models_response.get("models", [])

class GeminiService(AIService):
    def __init__(self):
        import warnings
        if not AI_API_KEY:
            raise ValueError("AI_API_KEY is required when AI_PROVIDER=gemini")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import google.generativeai as genai
        genai.configure(api_key=AI_API_KEY)
        self.genai = genai
    
    def _convert_messages_to_gemini(self, messages: List[dict]) -> List[dict]:
        """Convert Ollama-style messages to Gemini format"""
        gemini_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                # Gemini uses system instruction separately, but we can include it as a user message for now
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "user":
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})
            elif role == "tool":
                # Handle tool responses
                gemini_messages.append({"role": "user", "parts": [content]})
        
        return gemini_messages
    
    async def chat_stream(
        self,
        messages: List[dict],
        model: str,
        tools: List[dict] = None
    ) -> AsyncGenerator[str, None]:
        import asyncio
        gemini_messages = self._convert_messages_to_gemini(messages)
        model_instance = self.genai.GenerativeModel(model_name=model)
        
        # Run synchronous code in executor to avoid blocking event loop
        def generate():
            return model_instance.generate_content(
                [msg["parts"][0] for msg in gemini_messages],
                stream=True
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, generate)
        
        for chunk in response:
            if chunk.text:
                yield f"data: {json.dumps({'content': chunk.text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    async def chat(
        self,
        messages: List[dict],
        model: str,
        tools: List[dict] = None
    ) -> dict:
        import asyncio
        gemini_messages = self._convert_messages_to_gemini(messages)
        model_instance = self.genai.GenerativeModel(model_name=model)
        
        # Run synchronous code in executor
        def generate():
            return model_instance.generate_content(
                [msg["parts"][0] for msg in gemini_messages],
                stream=False
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, generate)
        
        # Return in a format compatible with what main.py expects
        return {
            "message": {
                "content": response.text if response.text else ""
            }
        }

    async def list_models(self) -> List[dict]:
        import asyncio
        import warnings
        loop = asyncio.get_event_loop()
        
        def list_models_sync():
            models = []
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                for m in self.genai.list_models():
                    if "generateContent" in m.supported_generation_methods:
                        models.append({"name": m.name})
            return models
        
        return await loop.run_in_executor(None, list_models_sync)

def get_ai_service() -> AIService:
    """Factory function to get the appropriate AI service"""
    if AI_PROVIDER == "gemini":
        return GeminiService()
    if AI_PROVIDER == "ollama":
        return OllamaService()
    raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}")
