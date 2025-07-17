import requests
import json

# API endpoint for user registration
url = "http://localhost:8000/auth/register"

# Specified user data
user_data = {
    "username": "user001",
    "password": "password"
}

def create_user():
    """Create the specified user"""
    try:
        print(f"Creating user: {user_data['username']}")
        response = requests.post(
            url,
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print(f"User created successfully: {result}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"User already exists: {response.text}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return False

if __name__ == "__main__":
    create_user()
