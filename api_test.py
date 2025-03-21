from pathlib import Path
import json
import requests
import datetime

API_KEY = Path('api_key.txt').read_text().strip()  # Replace with a valid API key
API_URL = "http://127.0.0.1:8000/logs/"

log_data = {
    "process_name": "TestProcess",
    "level": "INFO",
    "message": "This is a test log from Python",
    "timestamp": datetime.datetime.now().isoformat()
}

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(API_URL, json=log_data, headers=headers)

print(response.status_code)
print(response.json())
