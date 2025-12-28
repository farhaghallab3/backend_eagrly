from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    CONDITION_CHOICES = [('new','New'),('used','Used')]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('expired', 'Expired'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    # multiple images: we'll store first image as ImageField; extra images can be a JSON/Text field (urls)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    images = models.TextField(blank=True)  # optional JSON list of URLs
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    university = models.CharField(max_length=255, blank=True)
    faculty = models.CharField(max_length=255, blank=True)
    governorate = models.CharField(max_length=255, blank=True, default='')
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Ad expiration tracking
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

