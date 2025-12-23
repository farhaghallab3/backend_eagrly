import requests
import json

# Simple test to check if endpoints are working
print("Testing token endpoint...")

response = requests.post('http://127.0.0.1:8000/api/users/token/', json={
    "username": "admin",
    "password": "admin123"
})

print(f"Token response status: {response.status_code}")
print(f"Token response: {response.text}")

if response.status_code == 200:
    print("Login successful!")
else:
    print("Login failed, trying without password...")

    response2 = requests.post('http://127.0.0.1:8000/api/users/token/', json={
        "username": "admin",
        "password": ""
    })

    print(f"Token response 2 status: {response2.status_code}")
    print(f"Token response 2: {response2.text}")
