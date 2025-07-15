"""
This script tests the Japanese layout command detection in both frontend and backend code.
It doesn't make actual API calls but simulates the command detection logic.
"""

import re
import json

# Test Japanese layout commands
test_commands = [
    "springレイアウトを適応させてください",
    "円形レイアウトに変更してください",
    "ランダムレイアウトを適用",
    "スペクトルレイアウトを適用してください",
    "カマダカワイレイアウトを適用",
    "フルクターマンレイアウトを適用"
]

# Expected layout types for each command
expected_layouts = [
    "spring",
    "circular",
    "random",
    "spectral",
    "kamada_kawai",
    "fruchterman_reingold"
]

def test_frontend_detection(command):
    """
    Test the frontend detection logic for Japanese layout commands.
    This simulates the logic in NetworkChatPage.jsx.
    """
    # Check if the message is a command to change the layout (in English or Japanese)
    if ((command.lower().find('change') != -1 and command.lower().find('layout') != -1) or
        (command.find('レイアウト') != -1 and (command.find('適応') != -1 or command.find('変更') != -1 or command.find('適用') != -1))):
        
        # Determine layout type from message (English or Japanese)
        layout_type = "spring"  # Default
        message = command.lower()
        
        if message.find('circular') != -1 or command.find('円形') != -1:
            layout_type = "circular"
        elif message.find('random') != -1 or command.find('ランダム') != -1:
            layout_type = "random"
        elif message.find('spectral') != -1 or command.find('スペクトル') != -1:
            layout_type = "spectral"
        elif message.find('shell') != -1 or command.find('殻') != -1:
            layout_type = "shell"
        elif message.find('spring') != -1 or command.find('スプリング') != -1:
            layout_type = "spring"
        elif message.find('kamada') != -1 or command.find('カマダ') != -1:
            layout_type = "kamada_kawai"
        elif message.find('fruchterman') != -1 or command.find('フルクターマン') != -1:
            layout_type = "fruchterman_reingold"
        elif message.find('community') != -1 or command.find('コミュニティ') != -1:
            layout_type = "community"
            
        return layout_type
    else:
        return None

def test_backend_detection(command):
    """
    Test the backend detection logic for Japanese layout commands.
    This simulates the logic in network_chat.py.
    """
    # Check if the message is a command to change the layout
    if re.search(r'(change|apply).*layout|レイアウト.*(適応|変更|適用)', command, re.IGNORECASE):
        # Determine layout type from message
        layout_type = "spring"  # Default
        
        if re.search(r'circular|円形', command, re.IGNORECASE):
            layout_type = "circular"
        elif re.search(r'random|ランダム', command, re.IGNORECASE):
            layout_type = "random"
        elif re.search(r'spectral|スペクトル', command, re.IGNORECASE):
            layout_type = "spectral"
        elif re.search(r'shell|殻', command, re.IGNORECASE):
            layout_type = "shell"
        elif re.search(r'spring|スプリング', command, re.IGNORECASE):
            layout_type = "spring"
        elif re.search(r'kamada|カマダ', command, re.IGNORECASE):
            layout_type = "kamada_kawai"
        elif re.search(r'fruchterman|フルクターマン', command, re.IGNORECASE):
            layout_type = "fruchterman_reingold"
        elif re.search(r'community|コミュニティ', command, re.IGNORECASE):
            layout_type = "community"
            
        return layout_type
    else:
        return None

def main():
    """Main test function"""
    print("Testing Japanese layout command detection in code...")
    
    # Test frontend detection
    print("\n=== Frontend Detection Tests ===")
    frontend_results = []
    for i, command in enumerate(test_commands):
        detected_layout = test_frontend_detection(command)
        expected_layout = expected_layouts[i]
        result = detected_layout == expected_layout
        frontend_results.append(result)
        
        status = "PASSED" if result else "FAILED"
        print(f"{status}: '{command}' -> Expected: '{expected_layout}', Detected: '{detected_layout}'")
    
    # Test backend detection
    print("\n=== Backend Detection Tests ===")
    backend_results = []
    for i, command in enumerate(test_commands):
        detected_layout = test_backend_detection(command)
        expected_layout = expected_layouts[i]
        result = detected_layout == expected_layout
        backend_results.append(result)
        
        status = "PASSED" if result else "FAILED"
        print(f"{status}: '{command}' -> Expected: '{expected_layout}', Detected: '{detected_layout}'")
    
    # Print summary
    print("\n=== Test Summary ===")
    frontend_passed = all(frontend_results)
    backend_passed = all(backend_results)
    
    print(f"Frontend Detection: {'PASSED' if frontend_passed else 'FAILED'}")
    print(f"Backend Detection: {'PASSED' if backend_passed else 'FAILED'}")
    
    if frontend_passed and backend_passed:
        print("\nAll tests passed! Japanese layout commands are correctly detected in both frontend and backend code.")
    else:
        print("\nSome tests failed. Please check the logs above for details.")
    
    # Write results to file
    with open("test_results.log", "w") as log_file:
        log_file.write("Testing Japanese layout command detection in code...\n")
        
        log_file.write("\n=== Frontend Detection Tests ===\n")
        for i, command in enumerate(test_commands):
            detected_layout = test_frontend_detection(command)
            expected_layout = expected_layouts[i]
            result = detected_layout == expected_layout
            status = "PASSED" if result else "FAILED"
            log_file.write(f"{status}: '{command}' -> Expected: '{expected_layout}', Detected: '{detected_layout}'\n")
        
        log_file.write("\n=== Backend Detection Tests ===\n")
        for i, command in enumerate(test_commands):
            detected_layout = test_backend_detection(command)
            expected_layout = expected_layouts[i]
            result = detected_layout == expected_layout
            status = "PASSED" if result else "FAILED"
            log_file.write(f"{status}: '{command}' -> Expected: '{expected_layout}', Detected: '{detected_layout}'\n")
        
        log_file.write("\n=== Test Summary ===\n")
        log_file.write(f"Frontend Detection: {'PASSED' if frontend_passed else 'FAILED'}\n")
        log_file.write(f"Backend Detection: {'PASSED' if backend_passed else 'FAILED'}\n")
        
        if frontend_passed and backend_passed:
            log_file.write("\nAll tests passed! Japanese layout commands are correctly detected in both frontend and backend code.\n")
        else:
            log_file.write("\nSome tests failed. Please check the logs above for details.\n")

if __name__ == "__main__":
    main()
