import requests
import json

# First, check what products exist
products_response = requests.get('http://127.0.0.1:8000/api/products/')
if products_response.status_code == 200:
    products_data = products_response.json()
    print("Current products in database:")
    results = products_data.get('results', [])
    print(f"Total: {len(results)}")
    for product in results:
        print(f"  - ID: {product['id']}, Title: {product['title']}, Seller: {product.get('seller', 'Unknown')}, Status: {product.get('status', 'Unknown')}")
else:
    print("Could not fetch products")

print("\nTesting chatbot API...")

# Test calculator search
response = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
    "message": "Do you have a calculator?"
})

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Reply: {data.get('reply', '')}")

    products = data.get('products', [])
    print(f"Products in chatbot response: {len(products)}")

    # Debug the response
    print("Full response:", json.dumps(data, indent=2))

else:
    print(f"Error: {response.text}")
