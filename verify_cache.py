import requests
import json
import time

def test_cache():
    url = "http://127.0.0.1:5001/api/search"
    query = "Alexandria Ocasio-Cortez"
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}
    
    print(f"\n--- Request 1: '{query}' (Should hit API and cache) ---")
    start = time.time()
    response1 = requests.post(url, json=payload, headers=headers)
    duration1 = time.time() - start
    
    if response1.status_code == 200:
        print(f"Success. Duration: {duration1:.2f}s")
        # print("Result:", json.dumps(response1.json(), indent=2))
    else:
        print(f"Error: {response1.status_code}")
        print(response1.text)
        return

    print("\n--- Request 2: '{query}' (Should hit Cache) ---")
    start = time.time()
    response2 = requests.post(url, json=payload, headers=headers)
    duration2 = time.time() - start
    
    if response2.status_code == 200:
        print(f"Success. Duration: {duration2:.2f}s")
        if duration2 < duration1:
            print(">> CACHE HIT CONFIRMED (Faster response)")
        else:
            print(">> WARNING: Response time not significantly faster.")
    else:
        print(f"Error: {response2.status_code}")
        print(response2.text)

if __name__ == "__main__":
    test_cache()
