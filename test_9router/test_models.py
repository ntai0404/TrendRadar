import requests
import time

API_KEY = "sk-3970b0ca3a786f01-2cfii4-d6fc14b4"
API_BASE = "http://localhost:20128/v1/chat/completions"

models = [
    "ag/gemini-3.1-pro-high",
    "ag/gemini-3.1-pro-low",
    "ag/gemini-3-flash",
    "ag/claude-sonnet-4-6",
    "ag/claude-opus-4-6-thinking",
    "ag/gpt-oss-128b-medium"
]

def test_model(model_name):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hello, simply reply with 'Hi' and nothing else."}],
        "max_tokens": 10,
        "stream": True
    }
    
    print(f"Testing {model_name}...")
    start_time = time.time()
    try:
        response = requests.post(API_BASE, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start_time
        if response.status_code == 200:
            try:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"✅ SUCCESS: {model_name} (took {elapsed:.2f}s) -> Reply: {content.strip()}")
            except Exception as e:
                print(f"❌ JSON ERROR: {model_name} -> Raw response: '{response.text}'")
        else:
            print(f"❌ ERROR: {model_name} (Status: {response.status_code}) -> {response.text}")
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: {model_name} did not respond within 30 seconds.")
    except Exception as e:
        print(f"❌ ERROR: {model_name} -> {str(e)}")
    print("-" * 50)

if __name__ == "__main__":
    print("=======================================")
    print("Testing 9router models locally...")
    print("=======================================\n")
    for model in models:
        test_model(model)
