from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied, ValidationError, APIException
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from apps.common.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin, IsOwnerOrAdminOrActiveProduct
from apps.notifications.models import Notification
from .statistics import StatisticsMixin

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.prefetch_related('product_set').all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def products(self, request, pk=None):
        """Get all products in a specific category"""
        try:
            category = self.get_object()
        except:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        products = Product.objects.filter(category=category, status='active').select_related('category', 'seller')
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

class ProductViewSet(StatisticsMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('category', 'seller')
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact'],
        'price': ['exact', 'lt', 'gt'],
        'university': ['exact'],
        'faculty': ['exact'],
        'status': ['exact'],
        'seller__id': ['exact'],
    }
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at']

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]
        elif self.action == 'retrieve':
            return [permissions.AllowAny(), IsOwnerOrAdminOrActiveProduct()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        qs = Product.objects.all().select_related('category', 'seller').order_by('-created_at')
        user = self.request.user

        if self.action == 'list':
            # Admin users see all products for admin dashboard, others see active products for browsing
            if user.is_authenticated and user.role == 'admin':
                return qs
            return qs.filter(status='active')

        if self.action == 'retrieve':
            # For retrieve, show active products to everyone, plus allow owners to see their own products regardless of status
            if user.is_authenticated:
                return qs.filter(Q(status='active') | Q(seller=user))
            return qs.filter(status='active')

        # For update/delete:
        if user.is_authenticated and user.role == 'admin':
            return qs

        # user can only manage their own products
        return qs.filter(seller=user).select_related('category')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # This will raise ValidationError for field errors

        user = request.user

        # Check ad limits before saving
        current_product_count = Product.objects.filter(seller=user).count()

        # Admin users have unlimited ads
        if user.role == 'admin':
            serializer.save(seller=user, status='active')
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # Allow first 2 products as trial (new users get 2 free ads)
        if current_product_count < 2:
            serializer.save(seller=user, status='pending')
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # Check active package for additional products (Subscription Model - Concurrent Limit)
        has_active_package = (
            user.active_package and
            user.package_expiry and
            user.package_expiry >= timezone.now()
        )

        if has_active_package:
            # Calculate remaining ads in package (total limit - current usage)
            # Note: current_product_count includes ALL products.
            # If standard is Limit = Total Active Products, use that.
            # Assuming Package Limit applies to Total products count.
            if current_product_count < user.active_package.ad_limit:
                serializer.save(seller=user, status='pending')
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # Check free ads remaining (Credit Model - Consumable)
        if user.free_ads_remaining > 0:
            user.free_ads_remaining -= 1
            user.save()
            serializer.save(seller=user, status='pending')
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # No ads remaining - return custom 400 response
        return Response(
            {'code': 'ad_limit_exceeded', 'message': 'You have reached your ad limit. Please purchase a package to add more products.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance  # the product being updated
        requested_status = self.request.data.get('status')
        old_status = instance.status

        # If the user is admin, they can do anything
        if user.role == 'admin':
            serializer.save()

            # Create notification if product was approved (status changed from pending to active)
            if old_status == 'pending' and serializer.instance.status == 'active':
                Notification.objects.create(
                    user=instance.seller,
                    notification_type='product_approved',
                    title='Product Approved',
                    message=f'Your product "{instance.title}" has been approved and is now active.',
                    product=instance
                )
            # Create notification if product was rejected
            elif old_status == 'pending' and serializer.instance.status in ['rejected', 'inactive']:
                Notification.objects.create(
                    user=instance.seller,
                    notification_type='product_rejected',
                    title='Product Rejected',
                    message=f'Your product "{instance.title}" was not approved. Please review and update it.',
                    product=instance
                )
            return

        # If the user is the owner
        if instance.seller == user:
            # Any edit by the user resets the status to pending for admin approval
            serializer.save(status='pending')
            return

        raise PermissionDenied('You do not have permission to edit this product.')

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_products(self, request):
        # Return all products for the authenticated user, regardless of status (for dashboard)
        qs = Product.objects.filter(seller=request.user).select_related('category')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
