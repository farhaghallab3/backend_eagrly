from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'product_count', 'products']

    def get_product_count(self, obj):
        return obj.product_set.count()

    def get_products(self, obj):
        # Return list of product IDs for this category
        return list(obj.product_set.values_list('id', flat=True))

class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'condition', 'image', 'images', 'category', 'seller', 'university', 'faculty', 'governorate', 'is_featured', 'status', 'is_active', 'created_at', 'updated_at', 'category_name', 'approved_at', 'expires_at', 'days_remaining', 'is_expired']
        read_only_fields = ('seller','created_at','updated_at', 'approved_at', 'expires_at')

    def to_internal_value(self, data):
        # Handle category field - allow name or ID
        category_data = data.get('category')
        if category_data is not None:
            # Try to convert to int if it's a string
            try:
                category_id = int(category_data)
                # Check if the category exists with this ID
                if not Category.objects.filter(id=category_id).exists():
                    raise serializers.ValidationError({'category': f'Category with id {category_id} does not exist.'})
                # Keep the ID
                data = data.copy()
                data['category'] = category_id
            except (ValueError, TypeError):
                # It's a string name - create or get the category
                category, created = Category.objects.get_or_create(
                    name=str(category_data),
                    defaults={'description': ''}
                )
                data = data.copy()
                data['category'] = category.id

        return super().to_internal_value(data)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user and not request.user.is_staff:
            # For non-staff users, status is set automatically, so remove it from input fields
            self.fields.pop('status', None)

    def get_seller(self, obj):
        if obj.seller:
            return {
                "id": obj.seller.id,
                "email": obj.seller.email,
                "first_name": obj.seller.first_name,
                "phone": getattr(obj.seller, "phone", None)
            }
        return None

    def get_is_active(self, obj):
        return obj.status == 'active'

    def get_days_remaining(self, obj):
        """Calculate days remaining until ad expires."""
        if obj.expires_at:
            remaining = obj.expires_at - timezone.now()
            return max(0, remaining.days)
        return None

    def get_is_expired(self, obj):
        """Check if ad has expired."""
        if obj.expires_at:
            return timezone.now() > obj.expires_at
        return False

    def validate_status(self, value):
        """Ensure status is one of the allowed STATUS_CHOICES on Product."""
        if value:  # Only validate if value is provided
            allowed = [c[0] for c in Product.STATUS_CHOICES]
            if value not in allowed:
                raise serializers.ValidationError(f"status must be one of {allowed}")
        return value

    def validate(self, data):
        # For non-staff users, status field should not be required during validation
        request = self.context.get('request')
        if request and request.user and not request.user.is_staff:
            # Remove status from validation if it's empty for non-staff
            if 'status' in data and not data['status']:
                data.pop('status', None)
        return data
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email")
