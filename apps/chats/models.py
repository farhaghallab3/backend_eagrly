from django.db import models
from django.conf import settings

class Chat(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Chat {self.id} - {self.product}'

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
