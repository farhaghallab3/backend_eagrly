#!/usr/bin/env python
import os
import sys
import django
import requests
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

# Now test the API - note: this will work if the server is running
# But for direct testing, let's simulate the view call instead

from rest_framework.test import APIRequestFactory
from apps.products.views import ProductViewSet

# Create a factory
factory = APIRequestFactory()

# Create an anonymous request
request = factory.get('/api/products/9/')

# Create viewset instance
viewset = ProductViewSet()
viewset.action = 'retrieve'
viewset.request = request
viewset.kwargs = {'pk': '9'}

# Get permissions
perms = viewset.get_permissions()
print(f"Permissions for retrieve: {[p.__class__.__name__ for p in perms]}")

# Get queryset
try:
    qs = viewset.get_queryset()
    product = qs.filter(id=9).first()
    print(f"Product found in queryset: {product is not None}")
    if product:
        print(f"Product status: {product.status}")
        print(f"Product seller: {product.seller.username if product.seller else 'None'}")
except Exception as e:
    print(f"Error in get_queryset: {e}")

# Test permissions directly
from apps.common.permissions import IsOwnerOrAdminOrActiveProduct
from django.contrib.auth.models import AnonymousUser
from apps.products.models import Product

# Get the actual product
product = Product.objects.filter(id=9).first()

# Create permission instance
perm = IsOwnerOrAdminOrActiveProduct()

# Create mock request with anonymous user
class MockRequest:
    def __init__(self, user, method='GET'):
        self.user = user
        self.method = method

mock_request = MockRequest(AnonymousUser(), 'GET')

# Test permission
if product:
    allowed = perm.has_object_permission(mock_request, viewset, product)
    print(f"Anonymous user allowed to view product 9 (status: {product.status}): {allowed}")

    # Also test with an authenticated user who is not the owner
    from apps.users.models import User
    other_user = User.objects.filter(is_staff=False).exclude(username='FarhaGhallab').first()
    if other_user:
        mock_request_auth = MockRequest(other_user, 'GET')
        allowed_auth = perm.has_object_permission(mock_request_auth, viewset, product)
        print(f"Other authenticated user allowed to view product 9: {allowed_auth}")
    else:
        print("No other user found to test")

else:
    print("Product 9 not found")
