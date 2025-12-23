#!/usr/bin/env python
import os
import sys
import django
import requests
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from apps.users.views import UserViewSet
from apps.users.models import User

# Create a request factory
factory = APIRequestFactory()

# Create a mock request
request = factory.get('/api/users/me/')

# Create a test user (assuming there's at least one user in the system)
try:
    test_user = User.objects.filter(is_active=True).first()
    if not test_user:
        print("No active users found for testing")
        sys.exit(1)

    request.user = test_user

    # Create viewset instance
    viewset = UserViewSet()
    viewset.action = 'me'
    viewset.request = request

    # Test permissions
    perms = viewset.get_permissions()
    print(f"Permissions for 'me' action: {[p.__class__.__name__ for p in perms]}")

    # Test the view
    response = viewset.me(request)
    print("ME endpoint response:", response.data)

    print("SUCCESS: /api/users/me/ endpoint is working correctly")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
