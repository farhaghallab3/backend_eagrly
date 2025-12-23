from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('product_approved', 'Product Approved'),
        ('product_rejected', 'Product Rejected'),
        ('new_message', 'New Message'),
        ('system', 'System Notification'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional related objects
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    chat = models.ForeignKey('chats.Chat', on_delete=models.CASCADE, null=True, blank=True)
    message_obj = models.ForeignKey('chats.Message', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
