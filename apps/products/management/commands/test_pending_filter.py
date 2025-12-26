from django.core.management.base import BaseCommand
from apps.products.models import Product
from apps.users.models import User
from django.test import RequestFactory
from apps.products.views import ProductViewSet
from django.contrib.auth.models import AnonymousUser

class Command(BaseCommand):
    help = 'Test the products API filtering behavior'

    def handle(self, *args, **options):
        # Check database
        self.stdout.write("=== Database Check ===")
        pending_products = Product.objects.filter(status='pending')
        self.stdout.write(f"Pending products in DB: {pending_products.count()}")
        for p in pending_products:
            self.stdout.write(f"  - ID: {p.id}, Title: {p.title}, Status: {p.status}")

        all_products = Product.objects.all()
        self.stdout.write(f"\nTotal products in DB: {all_products.count()}")
        for p in all_products:
            self.stdout.write(f"  - ID: {p.id}, Title: {p.title}, Status: {p.status}")

        # Test API queryset
        self.stdout.write("\n=== API Queryset Test ===")
        factory = RequestFactory()

        # Test as admin
        admin_user = User.objects.filter(role='admin').first()
        if admin_user:
            self.stdout.write(f"\nTesting as admin user: {admin_user.email}")
            request = factory.get('/api/products/?status=pending')
            request.user = admin_user
            
            viewset = ProductViewSet()
            viewset.request = request
            viewset.action = 'list'
            
            qs = viewset.get_queryset()
            self.stdout.write(f"Queryset count (before filter): {qs.count()}")
            
            # Apply the filter manually to simulate DjangoFilterBackend
            filtered_qs = qs.filter(status='pending')
            self.stdout.write(f"Queryset count (after status=pending filter): {filtered_qs.count()}")
            for p in filtered_qs:
                self.stdout.write(f"  - ID: {p.id}, Title: {p.title}, Status: {p.status}")
        else:
            self.stdout.write("No admin user found!")

        # Test as anonymous user
        self.stdout.write("\n\nTesting as anonymous user:")
        request = factory.get('/api/products/?status=pending')
        request.user = AnonymousUser()

        viewset = ProductViewSet()
        viewset.request = request
        viewset.action = 'list'

        qs = viewset.get_queryset()
        self.stdout.write(f"Queryset count (before filter): {qs.count()}")

        # Apply the filter manually
        filtered_qs = qs.filter(status='pending')
        self.stdout.write(f"Queryset count (after status=pending filter): {filtered_qs.count()}")
