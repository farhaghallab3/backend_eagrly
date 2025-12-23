#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

from django.test import RequestFactory
from apps.products.views import ProductViewSet
from apps.products.models import Product, Category
from apps.users.models import User
from rest_framework.test import APIRequestFactory
import json

print("Testing free ads limit change...")

# Create a test user
try:
    test_user, created = User.objects.get_or_create(
        username='freeadstest',
        defaults={'email': 'freeads@test.com'}
    )
    if created:
        test_user.set_password('testpass')
        test_user.save()
        print("Created test user")
    else:
        # Clean up any existing products for this user
        Product.objects.filter(seller=test_user).delete()
        print("Cleaned up existing products for test user")

except Exception as e:
    print(f"Error setting up user: {e}")
    sys.exit(1)

# Get a category
try:
    category = Category.objects.first()
    if not category:
        category = Category.objects.create(name="Test Category", description="Test")
        print("Created test category")
except Exception as e:
    print(f"Error creating category: {e}")
    sys.exit(1)

# Test creating products
factory = APIRequestFactory()
viewset = ProductViewSet()

print("\n=== Testing Free Ads (should allow 2 free ads) ===")

# Test 1: First product (should be allowed as free)
print("Creating first product...")
request1 = factory.post('/api/products/', {
    'title': 'First Free Product',
    'description': 'Test product 1',
    'price': 10.0,
    'condition': 'new',
    'category': category.id
}, format='json')
request1.user = test_user

try:
    response1 = viewset.create(request1)
    print(f"✅ First product creation status: {response1.status_code}")
    if response1.status_code == 201:
        data1 = response1.data
        print(f"✅ First product created: {data1['title']} - Status: {data1['status']}")
    else:
        print(f"❌ First product creation failed: {response1.data}")
except Exception as e:
    print(f"❌ Error creating first product: {e}")

# Test 2: Second product (should also be allowed as free)
print("\nCreating second product...")
request2 = factory.post('/api/products/', {
    'title': 'Second Free Product',
    'description': 'Test product 2',
    'price': 20.0,
    'condition': 'used',
    'category': category.id
}, format='json')
request2.user = test_user

try:
    response2 = viewset.create(request2)
    print(f"✅ Second product creation status: {response2.status_code}")
    if response2.status_code == 201:
        data2 = response2.data
        print(f"✅ Second product created: {data2['title']} - Status: {data2['status']}")
    else:
        print(f"❌ Second product creation failed: {response2.data}")
except Exception as e:
    print(f"❌ Error creating second product: {e}")

# Test 3: Third product (should be blocked if no package/free ads)
print("\nCreating third product (should fail)...")
request3 = factory.post('/api/products/', {
    'title': 'Third Product - Should Fail',
    'description': 'Test product 3',
    'price': 30.0,
    'condition': 'new',
    'category': category.id
}, format='json')
request3.user = test_user

try:
    response3 = viewset.create(request3)
    print(f"Third product creation status: {response3.status_code}")
    if response3.status_code == 400:
        print("✅ Third product correctly blocked (ad limit exceeded)")
        print(f"   Error message: {response3.data}")
    else:
        print(f"❌ Third product should have been blocked but got status {response3.status_code}")
        if hasattr(response3, 'data'):
            print(f"   Response: {response3.data}")
except Exception as e:
    print(f"❌ Error creating third product: {e}")

# Check final product count
final_count = Product.objects.filter(seller=test_user).count()
print(f"\nFinal product count for test user: {final_count}")
print("✅ Test completed - New users should get 2 free ads instead of 1!")
