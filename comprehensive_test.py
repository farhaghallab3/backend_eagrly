#!/usr/bin/env python3
"""
Comprehensive test to verify the chatbot audio fix
"""
import requests
import json

def test_backend_fixes():
    """Test all scenarios to verify the fix"""
    
    API_URL = "http://127.0.0.1:8000/api/chatbot/"
    
    print("=== Testing Chatbot Audio Fix ===\n")
    
    # Test 1: Initial message (should return welcome)
    print("1. Testing initial message request:")
    response = requests.post(API_URL, json={"initial": True})
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test 2: Audio file (should process audio, not return welcome)
    print("2. Testing audio file request:")
    fake_audio = b"fake audio data for testing"
    files = {
        'audio': ('test.webm', fake_audio, 'audio/webm')
    }
    data = {'initial': False}
    
    try:
        response = requests.post(API_URL, files=files, data=data)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {result}")
        
        # Check if it's treating audio as initial message
        if result.get('reply') == "Looking for something specific? Can I help you?":
            print("   ❌ ISSUE: Audio request still returning initial welcome message")
            print("   This indicates the backend logic fix didn't work properly")
        else:
            print("   ✅ SUCCESS: Audio request is being processed correctly")
            
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 3: Regular text message
    print("3. Testing regular text message:")
    response = requests.post(API_URL, json={"message": "hello"})
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()

def check_server_status():
    """Check if server is running and responsive"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/", timeout=5)
        print(f"Server Status: {response.status_code}")
        return True
    except:
        print("Server is not responding. Make sure Django is running:")
        print("cd c:/Users/farha/Downloads/Graduation_project_ITI_Backend")
        print("python manage.py runserver")
        return False

if __name__ == "__main__":
    # Check server status first
    if not check_server_status():
        exit(1)
    
    # Run comprehensive tests
    test_backend_fixes()
    
    print("\n=== SUMMARY ===")
    print("If audio requests still return the welcome message, the fix needs:")
    print("1. Django server restart: python manage.py runserver")
    print("2. Verify the logic order in ChatbotAPIView.post():")
    print("   - Check for audio file FIRST")
    print("   - Then check for initial message")
    print("   - Then handle text messages")
    print("\nThe critical fix is moving audio_file check before is_initial check.")
