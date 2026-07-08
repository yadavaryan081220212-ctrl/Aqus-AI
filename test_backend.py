import requests
import json
import sys

print("Python version:", sys.version)
print("-" * 50)

# Test backend health
try:
    print("\n=== Testing backend health ===")
    response = requests.get("http://localhost:8000/api/models", timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test search functionality
    print("\n=== Testing search functionality ===")
    payload = {
        "messages": [{"role": "user", "content": "search cat in youtube"}],
        "model": "qwen2.5:0.5b",
        "use_web_search": False
    }
    
    print("Sending request...")
    with requests.post(
        "http://localhost:8000/api/chat/stream",
        json=payload,
        stream=True,
        timeout=60
    ) as r:
        print(f"Response status: {r.status_code}")
        print(f"Response headers: {dict(r.headers)}")
        
        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                print(f"RECV: {decoded}")
                sys.stdout.flush()
                
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
