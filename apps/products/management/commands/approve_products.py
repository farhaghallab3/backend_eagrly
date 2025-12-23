from django.core.management.base import BaseCommand
from apps.products.models import Category, Product

class Command(BaseCommand):
    help = 'Approve pending products - changes status from pending to active'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Approve all pending products')
        parser.add_argument('--id', type=int, help='Approve product with specific ID')

    def handle(self, *args, **options):
        if options['id']:
            # Approve specific product
            try:
                product = Product.objects.get(id=options['id'])
                if product.status == 'pending':
                    product.status = 'active'
                    product.save()
                    self.stdout.write(self.style.SUCCESS(f"Approved product '{product.title}' - now active for AI search!"))
                else:
                    self.stdout.write(f"Product '{product.title}' is already {product.status}")
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Product with ID {options['id']} not found"))
        elif options['all']:
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
                self.stdout.write('Use --id <ID> to approve specific product')
                pending_list = Product.objects.filter(status='pending').values_list('id', 'title')
                self.stdout.write('Pending products:')
                for pid, title in pending_list:
                    self.stdout.write(f'  • ID {pid}: {title}')
            else:
                self.stdout.write(self.style.SUCCESS('All products are approved and active!'))
