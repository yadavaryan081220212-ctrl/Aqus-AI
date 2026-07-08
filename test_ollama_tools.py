import asyncio
import ollama
import json

async def test_ollama_tools():
    print("Testing Ollama tools with qwen2.5:0.5b...")
    
    client = ollama.AsyncClient()
    
    tools = [
        {
            "name": "open_url",
            "description": "Open a URL in the default web browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to open"
                    }
                },
                "required": ["url"]
            }
        }
    ]
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Use the open_url tool when asked to open a website."
        },
        {
            "role": "user",
            "content": "Open youtube.com"
        }
    ]
    
    print("Calling ollama.chat...")
    response = await client.chat(
        model="qwen2.5:0.5b",
        messages=messages,
        tools=tools,
        stream=False
    )
    
    print(f"\nFull response type: {type(response)}")
    print(f"Full response: {json.dumps(response, indent=2, default=str)}")
    
    print(f"\nResponse message: {response.message}")
    print(f"Has tool_calls? {hasattr(response.message, 'tool_calls')}")
    if hasattr(response.message, 'tool_calls'):
        print(f"Tool calls: {response.message.tool_calls}")

if __name__ == "__main__":
    asyncio.run(test_ollama_tools())
