oimport os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

from apps.products.models import Category, Product
from apps.products.serializers import ProductSerializer
from rest_framework.test import APIRequestFactory

# Test getting products for a category
factory = APIRequestFactory()
request = factory.get('/api/categories/7/products/')

# Get category with id 7
try:
    category = Category.objects.get(id=7)
    print(f"Category: {category.name}")

    # Get active products for this category
    products = Product.objects.filter(category=category, status='active')
    print(f"Found {products.count()} active products")

    # Serialize the products
    serializer = ProductSerializer(products, many=True, context={'request': request})
    print("Products data:")
    for product in serializer.data:
        print(f"  - ID: {product['id']}, Title: {product['title']}, Status: {product['status']}")

except Category.DoesNotExist:
    print("Category with ID 7 not found")
except Exception as e:
    print(f"Error: {e}")
