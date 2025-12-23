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

from apps.chatbot.views import search_products
from apps.users.models import User

print("Testing search function directly...")

# Test with admin user (empty university/faculty)
admin = User.objects.get(username='admin')
print(f"Admin user: university='{admin.university}', faculty='{admin.faculty}'")

# Test search for calculator
results = search_products("calculator", admin)
print(f"\nSearch for 'calculator' returned {len(results)} products:")
for product in results:
    print(f"  - {product['title']} (${product['price']}) - {product['university']} - {product['faculty']}")

# Test search for calc
results2 = search_products("calc", admin)
print(f"\nSearch for 'calc' returned {len(results2)} products:")
for product in results2:
    print(f"  - {product['title']} (${product['price']}) - {product['university']} - {product['faculty']}")
