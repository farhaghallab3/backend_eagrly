from django.db import models
from django.conf import settings

class Package(models.Model):
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_in_days = models.PositiveIntegerField()
    ad_limit = models.PositiveIntegerField()
    featured_ad_limit = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Payment(models.Model):
    PAYMENT_METHODS = [('credit','Credit Card'),('paypal','PayPal'),('cash','Cash'),('wallet','Mobile Wallet'),('bank','Bank Transfer')]
    STATUS_CHOICES = [('pending','Pending'),('completed','Completed'),('failed','Failed'),('cancelled','Cancelled')]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='credit')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    response_data = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.status}"

