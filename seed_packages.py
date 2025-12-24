import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "classifieds.settings")
django.setup()

from apps.payments.models import Package

packages = [
    {
        "name": "Plus",
        "price": 9.99,
        "duration_in_days": 30,
        "ad_limit": 10,
        "featured_ad_limit": 1,
        "description": "Great for starters. Publish up to 10 ads.",
    },
    {
        "name": "Premium",
        "price": 19.99,
        "duration_in_days": 30,
        "ad_limit": 50,
        "featured_ad_limit": 5,
        "description": "Best value. Publish up to 50 ads and get 5 featured.",
    },
    {
        "name": "VIP",
        "price": 49.99,
        "duration_in_days": 60,
        "ad_limit": 999,
        "featured_ad_limit": 20,
        "description": "Unlimited potential. Access all features without limits.",
    },
]

for pkg_data in packages:
    package, created = Package.objects.get_or_create(
        name=pkg_data["name"],
        defaults=pkg_data
    )
    if created:
        print(f"Created package: {package.name}")
    else:
        print(f"Package already exists: {package.name}")
        # Optionally update existing packages
        for key, value in pkg_data.items():
            setattr(package, key, value)
        package.save()
        print(f"Updated package: {package.name}")

print("Seeding complete.")
