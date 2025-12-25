
import os
import sys
# Configure Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

import sys
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.products.views import ProductViewSet
from apps.products.models import Product, Category
from apps.users.models import User
from apps.notifications.models import Notification

def verify_notification():
    print("Notification Verification Script...")
    
    # 1. Setup Users
    user, _ = User.objects.get_or_create(username='notify_user', email='notify@example.com')
    user.role = 'user'
    user.save()
    
    admin, _ = User.objects.get_or_create(username='notify_admin', email='notify_admin@example.com')
    admin.role = 'admin'
    admin.is_staff = True
    admin.save()
    
    # 2. Setup Category & Product
    category, _ = Category.objects.get_or_create(name="Notify Cat")
    product = Product.objects.create(
        title="Pending Product",
        description="Waiting for approval",
        price=50,
        condition="new",
        category=category,
        seller=user,
        status="pending"
    )
    
    print(f"Product created with status: {product.status}")
    
    # 3. Admin Updates Product to Active
    factory = APIRequestFactory()
    data = {'status': 'active'}
    request = factory.patch(f'/api/products/{product.id}/', data, format='json')
    force_authenticate(request, user=admin)
    
    viewset = ProductViewSet.as_view({'patch': 'partial_update'})
    
    try:
        response = viewset(request, pk=product.id)
        print(f"Update Response Code: {response.status_code}")
        if response.status_code not in [200, 204]:
            print(f"ERROR Response: {response.data}")
        
        # Reload product
        product.refresh_from_db()
        print(f"Product status after update: {product.status}")
        
        # 4. Check for Notification
        print(f"DEBUG: Checking notifications for user ID: {user.id} ({user.username})")
        all_notifications = Notification.objects.all()
        print(f"DEBUG: Total notifications in DB: {all_notifications.count()}")
        for n in all_notifications:
            print(f" - Notif: {n.title} (Type: {n.notification_type}) for User ID: {n.user.id}")

        notifications = Notification.objects.filter(user=user, notification_type='product_approved')
        if notifications.exists():
            print(f"✅ SUCCESS: Found {notifications.count()} notification(s) for user.")
            print(f"Title: {notifications.first().title}")
            print(f"Message: {notifications.first().message}")
        else:
            print("❌ FAILURE: No notification found for user.")
            
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == '__main__':
    # Redirect stdout to file
    with open('debug_log.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        verify_notification()
        sys.stdout = sys.__stdout__
    
    # Print content of log file
    with open('debug_log.txt', 'r', encoding='utf-8') as f:
        print(f.read())
