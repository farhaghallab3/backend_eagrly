from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message
from apps.users.serializers import UserSerializer
from apps.products.models import Product
from apps.products.serializers import ProductSerializer

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.id')
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('timestamp','sender')

class ChatSerializer(serializers.ModelSerializer):
    buyer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    seller = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Chat
        fields = ('id', 'product', 'buyer', 'seller', 'created_at')
        read_only_fields = ('created_at',)

class ChatReadSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'product', 'buyer', 'seller', 'messages', 'created_at', 'unread_count')
        read_only_fields = ('created_at',)

    def get_unread_count(self, obj):
        """Count unread messages for the current user (messages not sent by them and not read)."""
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        user = request.user
        # Unread messages are those NOT sent by the current user and NOT read
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

