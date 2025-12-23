from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'is_read', 'created_at', 'product', 'chat', 'message_obj'
        ]
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Add product details if exists
        if instance.product:
            representation['product_title'] = instance.product.title
            representation['product_image'] = instance.product.image.url if instance.product.image else None

        return representation
