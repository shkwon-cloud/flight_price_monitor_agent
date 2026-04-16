import google.auth
import google.auth.transport.requests
import requests
import os

try:
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    token = credentials.token
except Exception as e:
    print(f"Error getting auth token: {e}")
    token = "INVALID"

def check_model(region, model, project):
    url = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/publishers/google/models/{model}:streamGenerateContent"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hi"}]}]
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Project: {project}, Region: {region}, Model: {model} => Status: {response.status_code}")
    if response.status_code != 200:
        print(response.json())

for p in [credentials.project_id]:
    check_model("us-central1", "gemini-1.5-flash-001", p)
    check_model("us-central1", "gemini-2.0-flash-lite-001", p)
    check_model("us-central1", "gemini-2.0-flash-lite-preview-02-05", p)
