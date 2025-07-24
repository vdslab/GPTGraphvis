import requests
import json

# API endpoint for user registration
url = "http://localhost:8000/auth/register"

# Test user data with email
user_data = {
    "username": "testuser2",
    "password": "testpassword",
    "email": "test2@example.com"
}

# Alternative test user data without email (in case the API doesn't require email)
user_data_no_email = {
    "username": "testuser2",
    "password": "testpassword"
}

def create_user():
    """Create a test user"""
    try:
        # First try with email
        print(f"Creating test user: {user_data['username']} (with email)")
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
            print(f"Error with email: {response.status_code} - {response.text}")
            
            # Try without email
            print(f"Trying without email: {user_data_no_email['username']}")
            response = requests.post(
                url,
                json=user_data_no_email,
                headers={"Content-Type": "application/json"}
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                print(f"User created successfully (without email): {result}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"User already exists: {response.text}")
                return True
            else:
                print(f"Error without email: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return False

if __name__ == "__main__":
    create_user()
