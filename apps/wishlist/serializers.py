from rest_framework import serializers
from .models import Wishlist
from apps.products.models import Product

class WishlistSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product')
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=12, decimal_places=2, read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product_id', 'product_title', 'product_price', 'product_image', 'created_at']
        read_only_fields = ('user', 'created_at')
