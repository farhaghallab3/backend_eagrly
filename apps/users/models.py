from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    # ERD fields: name (use first+last), email, password, university, faculty, phone, role, freeAdRemaining, activePackage, packageExpiry, createdAt, updatedAt
    location = models.CharField(max_length=255, blank=True)
    governorate = models.CharField(max_length=255, blank=True)
    university = models.CharField(max_length=255, blank=True)
    faculty = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    ROLE_CHOICES = [('user','User'),('admin','Admin')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    free_ads_remaining = models.PositiveIntegerField(default=0)
    active_package = models.ForeignKey(
    'payments.Package',
    on_delete=models.SET_NULL,
    null=True,
    blank=True)
    package_expiry = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Email verification fields
    is_email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=4, blank=True, null=True)
    email_otp_created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username
