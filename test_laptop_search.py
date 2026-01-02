import requests
import json

# Test specifically for laptop search
print("Testing laptop search specifically...")

response = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
    "message": "I need a laptop"
})

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Reply: {data.get('reply', '')}")

    products = data.get('products', [])
    print(f"Products in chatbot response: {len(products)}")
    
    # Show product details
    for product in products:
        print(f"  - ID: {product['id']}, Title: {product['title']}, Price: {product['price']}")

    print("\nFull response:")
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.text}")

# Also test with the exact title we know exists
print("\n" + "="*50)
print("Testing direct search for 'laptop'...")

response2 = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
    "message": "laptop"
})

print(f"Status: {response2.status_code}")

if response2.status_code == 200:
    data2 = response2.json()
    print(f"Reply: {data2.get('reply', '')}")

    products2 = data2.get('products', [])
    print(f"Products in chatbot response: {len(products2)}")
    
    # Show product details
    for product in products2:
        print(f"  - ID: {product['id']}, Title: {product['title']}, Price: {product['price']}")
