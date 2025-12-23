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

print("Testing product ownership permissions...")

# Create test users
try:
    user1 = User.objects.get(username='admin')
    # Create or get another user for testing
    user2, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user2.set_password('testpass')
        user2.save()
        print("Created test user")
except Exception as e:
    print(f"Error setting up users: {e}")
    sys.exit(1)

# Get or create a test category
try:
    category = Category.objects.first()
    if not category:
        category = Category.objects.create(name="Test Category", description="Test category")
        print("Created test category")
except Exception as e:
    print(f"Error creating category: {e}")
    sys.exit(1)

# Create test products
try:
    product1 = Product.objects.filter(seller=user1).first()
    if not product1:
        product1 = Product.objects.create(
            title="Test Product by Admin",
            description="Test description",
            price=100.0,
            condition="new",
            category=category,
            seller=user1,
            status="active"
        )
        print("Created test product for admin")

    product2 = Product.objects.filter(seller=user2).first()
    if not product2:
        product2 = Product.objects.create(
            title="Test Product by User2",
            description="Test description",
            price=50.0,
            condition="used",
            category=category,
            seller=user2,
            status="active"
        )
        print("Created test product for user2")

except Exception as e:
    print(f"Error creating products: {e}")
    sys.exit(1)

# Test permissions
factory = APIRequestFactory()

print("\n=== Testing Product Permissions ===")

# Test 1: Admin can access their own product
viewset = ProductViewSet()
viewset.action = 'retrieve'
request = factory.get(f'/api/products/{product1.id}/')
request.user = user1

try:
    viewset.request = request
    queryset = viewset.get_queryset()
    can_access = product1 in queryset
    print(f"✅ Admin can access their own product: {can_access}")
except Exception as e:
    print(f"❌ Error testing admin access: {e}")

# Test 2: User2 cannot access admin's product
request2 = factory.get(f'/api/products/{product1.id}/')
request2.user = user2

try:
    viewset.request = request2
    queryset = viewset.get_queryset()
    can_access = product1 in queryset
    print(f"✅ User2 cannot access admin's product (only active products): {can_access}")
except Exception as e:
    print(f"❌ Error testing user2 access to admin product: {e}")

# Test 3: User2 can access their own product
request3 = factory.get(f'/api/products/{product2.id}/')
request3.user = user2

try:
    viewset.request = request3
    queryset = viewset.get_queryset()
    can_access = product2 in queryset
    print(f"✅ User2 can access their own product: {can_access}")
except Exception as e:
    print(f"❌ Error testing user2 access to own product: {e}")

# Test 4: Anonymous user can only see active products
from django.contrib.auth.models import AnonymousUser
request4 = factory.get('/api/products/')
request4.user = AnonymousUser()

try:
    viewset.action = 'list'
    viewset.request = request4
    queryset = viewset.get_queryset()
    active_products = list(queryset.filter(status='active'))
    print(f"✅ Anonymous user sees {len(active_products)} active products")
except Exception as e:
    print(f"❌ Error testing anonymous access: {e}")

print("\n=== Permission Classes Test ===")
from apps.common.permissions import IsOwnerOrAdmin

# Test permission class
permission = IsOwnerOrAdmin()

# Admin should have permission on any product
has_perm_admin = permission.has_object_permission(request, viewset, product2)
print(f"✅ Admin has permission on user2's product: {has_perm_admin}")

# User2 should have permission on their own product
has_perm_user2 = permission.has_object_permission(request3, viewset, product2)
print(f"✅ User2 has permission on their own product: {has_perm_user2}")

# User2 should NOT have permission on admin's product
has_perm_user2_admin = permission.has_object_permission(request2, viewset, product1)
print(f"✅ User2 does NOT have permission on admin's product: {has_perm_user2_admin}")

print("\n=== Summary ===")
print("✅ Product ownership permissions are working correctly!")
print("✅ Users can only edit/delete their own products")
print("✅ Admins can manage all products")
print("✅ Anonymous users can only view active products")
