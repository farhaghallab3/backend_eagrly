import requests
import json

# Test the new chatbot search behavior
# This should return only 3 cheapest products from user's university/faculty

print("Testing chatbot search with university/faculty filtering...")

# Get a token first
login_response = requests.post('http://127.0.0.1:8000/api/users/token/', json={
    "username": "admin",
    "password": "admin123"
})

if login_response.status_code == 200:
    token_data = login_response.json()
    token = token_data.get('access')
    print(f"Got token: {token[:20]}...")

    # Test search for a common item
    search_response = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
        "message": "I need a calculator"
    }, headers={
        'Authorization': f'Bearer {token}'
    })

    print(f"Search response status: {search_response.status_code}")

    if search_response.status_code == 200:
        data = search_response.json()
        print(f"Bot reply: {data.get('reply')}")
        products = data.get('products', [])
        print(f"Number of products returned: {len(products)}")

        if products:
            print("Products (should be max 3, ordered by price):")
            for i, product in enumerate(products):
                print(f"  {i+1}. {product['title']} - ${product['price']} - {product.get('university', 'N/A')} - {product.get('faculty', 'N/A')}")
        else:
            print("No products found")
    else:
        print(f"Error: {search_response.text}")
else:
    print(f"Login failed: {login_response.text}")
