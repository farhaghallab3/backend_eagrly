import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

from apps.products.models import Product
from apps.users.models import User
from django.test import RequestFactory
from apps.products.views import ProductViewSet

# Check database
print("=== Database Check ===")
pending_products = Product.objects.filter(status='pending')
print(f"Pending products in DB: {pending_products.count()}")
for p in pending_products:
    print(f"  - ID: {p.id}, Title: {p.title}, Status: {p.status}")

all_products = Product.objects.all()
print(f"\nTotal products in DB: {all_products.count()}")
for p in all_products:
    print(f"  - ID: {p.id}, Title: {p.title}, Status: {p.status}")

# Test API queryset
print("\n=== API Queryset Test ===")
factory = RequestFactory()

# Test as admin
admin_user = User.objects.filter(role='admin').first()
if admin_user:
    print(f"\nTesting as admin user: {admin_user.email}")
    request = factory.get('/api/products/?status=pending')
    request.user = admin_user
    
    viewset = ProductViewSet()
    viewset.request = request
    viewset.action = 'list'
    
    qs = viewset.get_queryset()
    print(f"Queryset count (before filter): {qs.count()}")
    
    # Apply the filter manually to simulate DjangoFilterBackend
    filtered_qs = qs.filter(status='pending')
    print(f"Queryset count (after status=pending filter): {filtered_qs.count()}")
    for p in filtered_qs:
        print(f"  - ID: {p.id}, Title: {p.title}, Status: {p.status}")
else:
    print("No admin user found!")

# Test as anonymous user
print("\n\nTesting as anonymous user:")
from django.contrib.auth.models import AnonymousUser
request = factory.get('/api/products/?status=pending')
request.user = AnonymousUser()

viewset = ProductViewSet()
viewset.request = request
viewset.action = 'list'

qs = viewset.get_queryset()
print(f"Queryset count (before filter): {qs.count()}")

# Apply the filter manually
filtered_qs = qs.filter(status='pending')
print(f"Queryset count (after status=pending filter): {filtered_qs.count()}")
