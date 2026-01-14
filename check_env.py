from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

print("Keys in environment:")
keys = list(os.environ.keys())
filtered_keys = [k for k in keys if "API" in k or "KEY" in k]
print(filtered_keys)

if "API_KEY" in os.environ:
    print("API_KEY is present")
else:
    print("API_KEY is MISSING")
