import requests
import json
import time

# API endpoint for chat
url = "http://localhost:8000/network-chat/chat"

# Test user credentials
auth_url = "http://localhost:8000/auth/token"
auth_data = {
    "username": "testuser2",
    "password": "testpassword"
}

# Japanese layout commands to test
test_commands = [
    "springレイアウトを適応させてください",
    "円形レイアウトに変更してください",
    "ランダムレイアウトを適用",
    "スペクトルレイアウトを適用してください"
]

def get_token():
    """Get authentication token"""
    try:
        response = requests.post(
            auth_url,
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"Successfully obtained token: {token[:10]}...")
            return token
        else:
            print(f"Failed to get token: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        return None

def test_layout_command(command, token):
    """Test a layout command"""
    if not token:
        print("No token available, skipping test")
        return False
    
    try:
        # Prepare request data
        data = {
            "message": command,
            "history": []
        }
        
        # Set headers with token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # Send request
        print(f"\nTesting command: '{command}'")
        response = requests.post(url, json=data, headers=headers)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result['response']}")
            
            # Check if network update is present
            if result.get("network_update"):
                network_update = result["network_update"]
                print(f"Network update: {network_update}")
                
                # Check if layout type is correctly detected
                if network_update.get("type") == "layout":
                    layout_type = network_update.get("layout")
                    print(f"Detected layout type: {layout_type}")
                    
                    # Verify layout type based on command
                    if "spring" in command.lower() or "スプリング" in command:
                        return layout_type == "spring"
                    elif "円形" in command or "circular" in command:
                        return layout_type == "circular"
                    elif "ランダム" in command or "random" in command:
                        return layout_type == "random"
                    elif "スペクトル" in command or "spectral" in command:
                        return layout_type == "spectral"
                    else:
                        return False
                else:
                    print("No layout type in network update")
                    return False
            else:
                print("No network update in response")
                return False
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error testing command: {str(e)}")
        return False

def main():
    """Main test function"""
    # Open a log file
    with open("test_results.log", "w") as log_file:
        log_file.write("Starting Japanese layout command tests...\n")
        print("Starting Japanese layout command tests...")
        
        # Get token
        token = get_token()
        if not token:
            log_file.write("Failed to get token, cannot proceed with tests\n")
            print("Failed to get token, cannot proceed with tests")
            return
        
        # Wait for API to be fully ready
        log_file.write("Waiting for API to be fully ready...\n")
        print("Waiting for API to be fully ready...")
        time.sleep(2)
        
        # Test each command
        results = {}
        for command in test_commands:
            result = test_layout_command(command, token)
            results[command] = result
            # Log result
            log_file.write(f"\nTesting command: '{command}'\n")
            log_file.write(f"Result: {'PASSED' if result else 'FAILED'}\n")
            # Wait between requests
            time.sleep(1)
        
        # Print and log summary
        summary = "\n=== Test Results ===\n"
        log_file.write(summary)
        print(summary)
        
        all_passed = True
        for command, result in results.items():
            status = "PASSED" if result else "FAILED"
            result_line = f"{status}: {command}\n"
            log_file.write(result_line)
            print(result_line)
            if not result:
                all_passed = False
        
        if all_passed:
            final_message = "\nAll tests passed! Japanese layout commands are working correctly.\n"
            log_file.write(final_message)
            print(final_message)
        else:
            final_message = "\nSome tests failed. Please check the logs above for details.\n"
            log_file.write(final_message)
            print(final_message)

if __name__ == "__main__":
    main()
