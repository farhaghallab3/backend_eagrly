from django.core.management.base import BaseCommand
from apps.products.models import Category, Product
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Approve pending products for testing - activates products in the database'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Approve all pending products')

    def handle(self, *args, **options):
        if options['all']:
            # Approve all pending products
            pending_products = Product.objects.filter(status='pending')
            count = pending_products.update(status='active')
            self.stdout.write(self.style.SUCCESS(f'Approved {count} pending products - they are now active for the AI to find!'))
        else:
            # Show current status
            total = Product.objects.count()
            active = Product.objects.filter(status='active').count()
            pending = Product.objects.filter(status='pending').count()

            self.stdout.write('Product Status Summary:')
            self.stdout.write(f'  Total products: {total}')
            self.stdout.write(f'  Active products: {active} (visible to customers)')
            self.stdout.write(f'  Pending products: {pending} (waiting for approval)')

            if pending > 0:
                self.stdout.write(self.style.WARNING('\nUse --all to approve all pending products'))
                pending_list = Product.objects.filter(status='pending').values_list('title', flat=True)
                self.stdout.write('Pending products:')
                for title in pending_list:
                    self.stdout.write(f'  • {title}')
            else:
                self.stdout.write(self.style.SUCCESS('All products are approved and active!'))
