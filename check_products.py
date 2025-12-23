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

from apps.products.models import Product
from apps.users.models import User

print("Checking products and users...")

# Check admin user
try:
    admin = User.objects.get(username='admin')
    print(f"Admin user - University: '{admin.university}', Faculty: '{admin.faculty}'")
except:
    print("Admin user not found")

# Check products
active_products = Product.objects.filter(status='active')
print(f"\nTotal active products: {active_products.count()}")

print("\nFirst 10 active products:")
for product in active_products[:10]:
    print(f"  {product.title} - ${product.price} - University: '{product.university}' - Faculty: '{product.faculty}'")

# Check products with calculator in title
calc_products = Product.objects.filter(status='active', title__icontains='calculator')
print(f"\nCalculator products: {calc_products.count()}")
for product in calc_products:
    print(f"  {product.title} - ${product.price} - University: '{product.university}' - Faculty: '{product.faculty}'")
