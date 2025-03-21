import requests

API_URL = "http://127.0.0.1:8000/keys/"

response = requests.post(API_URL)

if response.status_code == 200:
    api_key = response.json()["key"]
    print("Generated API Key:", api_key)
else:
    print("Error:", response.status_code, response.json())
