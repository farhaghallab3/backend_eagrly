from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category
from apps.users.models import User
from apps.payments.models import Payment, Package


class StatisticsMixin:
    """Mixin to add statistics endpoints to viewsets"""
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def dashboard_stats(self, request):
        """
        Get overview statistics for the main admin dashboard
        """
        # Product statistics
        total_products = Product.objects.count()
        active_products = Product.objects.filter(status='active').count()
        pending_products = Product.objects.filter(status='pending').count()
        inactive_products = Product.objects.filter(status='inactive').count()
        
        # Products created in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        products_last_30_days = Product.objects.filter(created_at__gte=thirty_days_ago).count()
        
        # Top categories by product count
        top_categories = Category.objects.annotate(
            product_count=Count('product')
        ).order_by('-product_count')[:5].values('id', 'name', 'product_count')
        
        # Top sellers
        top_sellers = User.objects.annotate(
            product_count=Count('product')
        ).order_by('-product_count')[:5].values(
            'id', 'username', 'first_name', 'last_name', 'product_count'
        )
        
        # User statistics
        total_users = User.objects.count()
        users_last_30_days = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        
        # Payment statistics
        total_revenue = Payment.objects.filter(
            status__in=['COMPLETED', 'completed', 'active']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_last_30_days = Payment.objects.filter(
            start_date__gte=thirty_days_ago.date(),
            status__in=['COMPLETED', 'completed', 'active']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_payments = Payment.objects.filter(
            status__in=['COMPLETED', 'completed', 'active']
        ).count()
        
        pending_payments = Payment.objects.filter(
            status__in=['PENDING', 'pending']
        ).count()
        
        return Response({
            'products': {
                'total': total_products,
                'active': active_products,
                'pending': pending_products,
                'inactive': inactive_products,
                'last_30_days': products_last_30_days,
            },
            'categories': {
                'top_categories': list(top_categories),
            },
            'sellers': {
                'top_sellers': list(top_sellers),
            },
            'users': {
                'total': total_users,
                'last_30_days': users_last_30_days,
            },
            'revenue': {
                'total': float(total_revenue),
                'last_30_days': float(revenue_last_30_days),
                'total_payments': total_payments,
                'pending_payments': pending_payments,
            }
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def analytics(self, request):
        """
        Get detailed analytics data with time-series information
        """
        # Get date range from query params (default to last 30 days)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Product creation timeline (daily)
        product_timeline = Product.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Products by category
        products_by_category = Category.objects.annotate(
            product_count=Count('product')
        ).values('id', 'name', 'product_count').order_by('-product_count')
        
        # Products by status
        products_by_status = Product.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # User registration timeline (daily)
        user_timeline = User.objects.filter(
            date_joined__gte=start_date
        ).annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Products by university
        products_by_university = Product.objects.exclude(
            university=''
        ).values('university').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Revenue timeline (weekly for better visualization)
        revenue_timeline = Payment.objects.filter(
            start_date__gte=start_date.date(),
            status__in=['COMPLETED', 'completed', 'active']
        ).annotate(
            week=TruncWeek('start_date')
        ).values('week').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('week')
        
        # Revenue by payment method
        revenue_by_method = Payment.objects.filter(
            status__in=['COMPLETED', 'completed', 'active']
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Revenue by package
        revenue_by_package = Payment.objects.filter(
            status__in=['COMPLETED', 'completed', 'active']
        ).values('package__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Average transaction value
        avg_transaction = Payment.objects.filter(
            status__in=['COMPLETED', 'completed', 'active']
        ).aggregate(avg=Avg('amount'))['avg'] or 0
        
        # Top selling products (based on being in completed payments)
        # Note: This is a simplified version. In a real scenario, you'd have a sales/orders model
        top_products = Product.objects.filter(
            status='active'
        ).annotate(
            # Placeholder - in real app, you'd count actual sales
            views=Count('id')
        ).order_by('-created_at')[:10].values(
            'id', 'title', 'price', 'category__name'
        )
        
        return Response({
            'product_timeline': list(product_timeline),
            'products_by_category': list(products_by_category),
            'products_by_status': list(products_by_status),
            'products_by_university': list(products_by_university),
            'user_timeline': list(user_timeline),
            'revenue_timeline': [
                {
                    'week': item['week'].isoformat() if item['week'] else None,
                    'total': float(item['total']),
                    'count': item['count']
                }
                for item in revenue_timeline
            ],
            'revenue_by_method': [
                {
                    'method': item['payment_method'],
                    'total': float(item['total']),
                    'count': item['count']
                }
                for item in revenue_by_method
            ],
            'revenue_by_package': [
                {
                    'package': item['package__name'],
                    'total': float(item['total']),
                    'count': item['count']
                }
                for item in revenue_by_package
            ],
            'avg_transaction': float(avg_transaction),
            'top_products': list(top_products),
            'date_range': {
                'start': start_date.isoformat(),
                'end': timezone.now().isoformat(),
                'days': days
            }
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def approval_stats(self, request):
        """
        Get statistics related to product approval workflow
        """
        # Pending products grouped by date
        pending_products = Product.objects.filter(
            status='pending'
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Recently approved products (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recently_approved = Product.objects.filter(
            status='active',
            updated_at__gte=seven_days_ago
        ).count()
        
        # Average approval time (time between creation and last update for active products)
        # This is a simplified metric
        total_pending = Product.objects.filter(status='pending').count()
        
        # Pending products by seller
        pending_by_seller = Product.objects.filter(
            status='pending'
        ).values('seller__username', 'seller__id').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'pending_timeline': list(pending_products),
            'total_pending': total_pending,
            'recently_approved': recently_approved,
            'pending_by_seller': list(pending_by_seller),
        })
