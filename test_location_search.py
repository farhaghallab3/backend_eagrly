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

from apps.chatbot.views import search_products, parse_location_from_query
from apps.users.models import User

print("Testing location-based search...")

# Test location parsing
test_queries = [
    "ruler from giza",
    "calculator in cairo",
    "alexandria notebook",
    "pencil from alex",
    "book in giza",
    "normal calculator"
]

for query in test_queries:
    location = parse_location_from_query(query)
    print(f"Query: '{query}' -> Location: '{location}'")

print("\nTesting search function...")

# Test with admin user (empty university/faculty)
admin = User.objects.get(username='admin')
print(f"Admin user: university='{admin.university}', faculty='{admin.faculty}'")

# Test search for ruler from giza (should find no products)
results = search_products("ruler from giza", admin)
print(f"\nSearch for 'ruler from giza' returned {len(results)} products:")
for product in results:
    print(f"  - {product['title']} (${product['price']}) - {product['university']} - Location: {getattr(product, 'governorate', 'N/A')}")

# Test search for ruler from alexandria (should find the ruler)
results2 = search_products("ruler from alexandria", admin)
print(f"\nSearch for 'ruler from alexandria' returned {len(results2)} products:")
for product in results2:
    print(f"  - {product['title']} (${product['price']}) - {product['university']} - Location: {getattr(product, 'governorate', 'N/A')}")
