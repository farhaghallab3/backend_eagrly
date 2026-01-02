#!/usr/bin/env python3
"""
Test script that matches exactly what the frontend ChatbotWidget sends
"""
import requests
import json

def test_exact_frontend_request():
    """Test exactly what the frontend sends"""
    
    # Backend URL
    API_URL = "http://127.0.0.1:8000/api/chatbot/"
    
    # Create fake audio content (simulating what MediaRecorder creates)
    fake_audio_data = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x04\x00\x00\x00\x00\x00\x00\x00"
    
    # Prepare form data exactly like the frontend
    files = {
        'audio': ('voice_message.webm', fake_audio_data, 'audio/webm')
    }
    
    # This is what the frontend sends
    data = {
        'initial': False
    }
    
    # Don't set Content-Type manually - let requests handle multipart boundary
    headers = {
        'Accept': 'application/json',
    }
    
    print("=== Testing Exact Frontend Request ===")
    print(f"POST to: {API_URL}")
    print(f"Files: {files}")
    print(f"Data: {data}")
    print(f"Headers: {headers}")
    
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
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return None, str(e)

def test_with_token():
    """Test with authentication token like the frontend might use"""
    
    API_URL = "http://127.0.0.1:8000/api/chatbot/"
    
    # Get token from localStorage (simulate what frontend does)
    token = localStorage.getItem("token") if 'localStorage' in globals() else None
    
    fake_audio_data = b"fake audio data"
    
    files = {
        'audio': ('voice_message.webm', fake_audio_data, 'audio/webm')
    }
    
    data = {
        'initial': False
    }
    
    headers = {
        'Accept': 'application/json',
    }
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
        print(f"Using token: {token[:20]}...")
    
    try:
        response = requests.post(API_URL, files=files, data=data, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content: {response.text}")
        return response.status_code, response.text
    except Exception as e:
        print(f"Error: {e}")
        return None, str(e)

if __name__ == "__main__":
    # Test exact frontend request
    status, content = test_exact_frontend_request()
    
    print(f"\n=== Final Results ===")
    print(f"Status: {status}")
    print(f"Content: {content}")
