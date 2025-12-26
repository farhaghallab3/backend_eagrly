import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

from apps.users.models import User
from apps.users.serializers import UserSerializer

print("=== Testing User Role Serialization ===\n")

# Test admin user
admin = User.objects.filter(is_staff=True).first()
if not admin:
    admin = User.objects.filter(is_superuser=True).first()

if admin:
    print("Admin User:")
    print(f"  Email: {admin.email}")
    print(f"  is_staff: {admin.is_staff}")
    print(f"  is_superuser: {admin.is_superuser}")
    print(f"  Database role field: {admin.role}")
    
    serialized = UserSerializer(admin).data
    print(f"\n  Serialized data:")
    print(f"    role: {serialized.get('role')}")
    print(f"    is_staff: {serialized.get('is_staff')}")
    print(f"    is_superuser: {serialized.get('is_superuser')}")
    print(f"\n  Expected: role='admin', is_staff=True or is_superuser=True")
    print(f"  Actual: role='{serialized.get('role')}', is_staff={serialized.get('is_staff')}, is_superuser={serialized.get('is_superuser')}")
    
    if serialized.get('role') == 'admin':
        print("\n  [PASS] Admin user role is correct!")
    else:
        print("\n  [FAIL] Admin user role is incorrect!")
else:
    print("[FAIL] No admin user found")

print("\n" + "="*50 + "\n")

# Test regular user
regular = User.objects.filter(is_staff=False, is_superuser=False).first()
if regular:
    print("Regular User:")
    print(f"  Email: {regular.email}")
    print(f"  is_staff: {regular.is_staff}")
    print(f"  is_superuser: {regular.is_superuser}")
    print(f"  Database role field: {regular.role}")
    
    serialized = UserSerializer(regular).data
    print(f"\n  Serialized data:")
    print(f"    role: {serialized.get('role')}")
    print(f"    is_staff: {serialized.get('is_staff')}")
    print(f"    is_superuser: {serialized.get('is_superuser')}")
    print(f"\n  Expected: role='user', is_staff=False, is_superuser=False")
    print(f"  Actual: role='{serialized.get('role')}', is_staff={serialized.get('is_staff')}, is_superuser={serialized.get('is_superuser')}")
    
    if serialized.get('role') == 'user':
        print("\n  [PASS] Regular user role is correct!")
    else:
        print("\n  [FAIL] Regular user role is incorrect!")
else:
    print("[FAIL] No regular user found")

print("\n" + "="*50)
print("Test Complete!")
