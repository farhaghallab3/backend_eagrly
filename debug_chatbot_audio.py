#!/usr/bin/env python3
"""
Debug script to test chatbot audio endpoint and identify the 400 error
"""
import requests
import json
from pathlib import Path

def test_chatbot_audio_endpoint():
    """Test the chatbot endpoint with audio file"""
    
    # Backend URL
    API_URL = "http://127.0.0.1:8000/api/chatbot/"
    
    # Create a simple test audio file (just for testing the endpoint structure)
    # In real scenario, this would be a proper webm audio file
    test_audio_content = b"fake audio content for testing"
    
    # Prepare form data
    files = {
        'audio': ('test_voice_message.webm', test_audio_content, 'audio/webm')
    }
    
    data = {
        'initial': False
    }
    
    headers = {
        'Accept': 'application/json',
    }
    
    print("Testing chatbot audio endpoint...")
    print(f"POST to: {API_URL}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    print(f"Files: {files}")
    
    try:
        response = requests.post(API_URL, files=files, data=data, headers=headers, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except:
            print(response.text)
            
        return response.status_code, response.text
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to backend server")
        print("Make sure the Django server is running on http://127.0.0.1:8000")
        return None, "Connection Error"
    except Exception as e:
        print(f"\nERROR: {e}")
        return None, str(e)

def check_backend_status():
    """Check if backend server is running"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/", timeout=5)
        print(f"Backend Status: {response.status_code}")
        return True
    except:
        print("Backend server is not responding")
        return False

if __name__ == "__main__":
    print("=== Chatbot Audio Endpoint Debug ===\n")
    
    # Check backend status
    backend_running = check_backend_status()
    if not backend_running:
        print("\nPlease start the backend server first:")
        print("cd c:/Users/farha/Downloads/Graduation_project_ITI_Backend")
        print("python manage.py runserver")
        exit(1)
    
    # Test the audio endpoint
    status, content = test_chatbot_audio_endpoint()
    
    print(f"\n=== Results ===")
    print(f"Status Code: {status}")
    print(f"Content: {content}")
