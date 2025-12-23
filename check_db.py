import os
import django
from django.conf import settings
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classifieds.settings')
django.setup()

def check_database_schema():
    cursor = connection.cursor()

    # Get table schema
    cursor.execute("PRAGMA table_info(users_user);")
    columns = cursor.fetchall()

    print("Users Table Schema:")
    for col in columns:
        print(f"  {col[1]} - {col[2]} {'NOT NULL' if not col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")

    # Check if specific columns exist
    column_names = [col[1] for col in columns]
    required_columns = ['location', 'governorate']

    print(f"\nRequired columns check:")
    for col in required_columns:
        status = "✓ EXISTS" if col in column_names else "✗ MISSING"
        print(f"  {col}: {status}")

    cursor.close()

if __name__ == "__main__":
    check_database_schema()
