import requests
import json
import os

def test_search():
    url = "http://127.0.0.1:5001/api/search"
    payload = {"query": "Nancy Pelosi"}
    headers = {"Content-Type": "application/json"}
    
    print(f"Testing {url} with query '{payload['query']}'...")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error Response:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Failed to connect. Is the server running on port 5000?")

if __name__ == "__main__":
    test_search()
