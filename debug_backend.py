import asyncio
import ollama
import json
import sys

async def debug():
    print("=== DEBUG MODE ===")
    
    client = ollama.AsyncClient()
    
    # Explicit tool-calling system prompt
    system_prompt = """YOU MUST USE THE open_url TOOL!
YOU ARE A TOOL-USING BOT! WHEN USER SAYS 'OPEN WEBSITE', CALL open_url!
DO NOT JUST TALK—USE THE TOOL!

Available tool: open_url(url="https://...")
Always use this tool to open any website!"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "OPEN YOUTUBE.COM NOW!"}
    ]
    
    tools = [
        {
            "name": "open_url",
            "description": "Open a website in the browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL starting with http:// or https://"
                    }
                },
                "required": ["url"]
            }
        }
    ]
    
    print("\nCalling ollama.chat...")
    print(f"Messages: {json.dumps(messages, indent=2)}")
    print(f"Tools: {json.dumps(tools, indent=2)}")
    
    response = await client.chat(
        model="qwen2.5:0.5b",
        messages=messages,
        tools=tools,
        stream=False,
        options={"num_ctx": 4096, "temperature": 0.1}
    )
    
    print(f"\n=== Full Response ===")
    print(json.dumps(response, indent=4, default=str))
    
    print(f"\n=== Message Content ===")
    if isinstance(response, dict):
        msg = response.get("message", {})
        print(msg.get("content", "<empty>"))
        tool_calls = msg.get("tool_calls")
        print(f"\n=== Tool Calls ===")
        if tool_calls:
            print(json.dumps(tool_calls, indent=4))
        else:
            print("NO TOOL CALLS!")

if __name__ == "__main__":
    asyncio.run(debug())
