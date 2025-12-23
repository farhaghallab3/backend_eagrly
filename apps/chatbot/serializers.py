from rest_framework import serializers

class ChatbotSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
