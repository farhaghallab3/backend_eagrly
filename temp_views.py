from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from apps.common.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
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
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        qs = Product.objects.all().select_related('category', 'seller')
        user = self.request.user

        if self.action == 'list':
            # Authenticated users see their own products (active or pending), anonymous users see all active products
            if user.is_authenticated:
                return qs.filter(seller=user)
            return qs.filter(status='active')

        if self.action == 'retrieve':
            # For retrieve, show active products to everyone, plus allow owners to see their own products regardless of status
            if user.is_authenticated:
                return qs.filter(Q(status='active') | Q(seller=user))
            return qs.filter(status='active')

        # For update/delete: user can only manage their own products
        return qs.filter(seller=user).select_related('category')

    def perform_create(self, serializer):
        user = self.request.user
        # Optional: limit regular users to 2 products
        if not user.is_staff:
            count = Product.objects.filter(seller=user).count()
            if count >= 2:
                raise PermissionDenied("Regular users can only add up to 2 products.")

        # Set status to 'active' for staff, 'pending' for regular users
        status = 'active' if user.is_staff else 'pending'
        serializer.save(seller=user, status=status)

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance  # the product being updated
        requested_status = self.request.data.get('status')

        # If the user is staff, they can do anything
        if user.is_staff:
            serializer.save()
            return

        # If the user is the owner
        if instance.seller == user:
            if requested_status == 'active':
                serializer.save(status='pending')
            else:
                serializer.save()
                return

        raise PermissionDenied('You do not have permission to edit this product.')

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_products(self, request):
        # Return all products for the authenticated user, regardless of status (for dashboard)
        qs = Product.objects.filter(seller=request.user).select_related('category')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
