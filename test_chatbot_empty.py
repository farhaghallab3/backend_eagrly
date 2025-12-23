import requests
import json

# Test the chatbot starts empty

print("Testing chatbot initial load (should be empty)...")

# Test initial load - try without authentication first
initial_response = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
    "initial": True
})

print(f"Initial load status: {initial_response.status_code}")

if initial_response.status_code == 200:
    data = initial_response.json()
    print(f"Initial load reply: {data.get('reply')}")
    print(f"Initial load products: {len(data.get('products', []))}")
    print("Full initial response:", json.dumps(data, indent=2))
elif initial_response.status_code == 401:
    print("Authentication required for initial load - this is expected")
    print(f"Error: {initial_response.text}")
else:
    print(f"Unexpected error: {initial_response.text}")

print("\nTesting chatbot with user message...")

# For message testing, we need authentication. Let's try to get a token first
print("Attempting to get authentication token...")

# Try to login with a known user (assuming default password or check if we can get one)
login_response = requests.post('http://127.0.0.1:8000/api/users/token/', json={
    "username": "admin",
    "password": "admin123"  # Try common password
})

if login_response.status_code == 200:
    token_data = login_response.json()
    token = token_data.get('access')
    print(f"Got token: {token[:20]}...")

    # Test with a message using the token
    message_response = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
        "message": "Do you have calculators?"
    }, headers={
        'Authorization': f'Bearer {token}'
    })

    print(f"Message response status: {message_response.status_code}")

    if message_response.status_code == 200:
        data = message_response.json()
        print(f"Message reply: {data.get('reply')}")
        print(f"Message products: {len(data.get('products', []))}")
        print("Full message response:", json.dumps(data, indent=2))
    else:
        print(f"Error: {message_response.text}")
else:
    print(f"Login failed: {login_response.text}")
    print("Cannot test authenticated message without valid token")
