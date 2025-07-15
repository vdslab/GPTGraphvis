import requests
import json

# API endpoint
url = "http://localhost:8000/network-layout/apply"

# Sample network data
data = {
    "nodes": [
        {"id": "1", "label": "Node 1"},
        {"id": "2", "label": "Node 2"},
        {"id": "3", "label": "Node 3"},
        {"id": "4", "label": "Node 4"},
        {"id": "5", "label": "Node 5"}
    ],
    "edges": [
        {"source": "1", "target": "2"},
        {"source": "1", "target": "3"},
        {"source": "2", "target": "3"},
        {"source": "3", "target": "4"},
        {"source": "4", "target": "5"},
        {"source": "5", "target": "1"}
    ],
    "layout": "circular",
    "layout_params": {}
}

# Get token (you'll need to replace this with a valid token)
auth_url = "http://localhost:8000/auth/token"
auth_data = {
    "username": "testuser",
    "password": "testpassword"
}

try:
    # Try to get a token
    auth_response = requests.post(
        auth_url,
        data=auth_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if auth_response.status_code == 200:
        token = auth_response.json().get("access_token")
        print(f"Successfully obtained token: {token[:10]}...")
        
        # Make request with token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        # Print response
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    else:
        print(f"Failed to get token: {auth_response.text}")
        
        # Try without authentication for testing
        print("Trying without authentication...")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        
        # Print response
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
            
except Exception as e:
    print(f"Error: {str(e)}")
