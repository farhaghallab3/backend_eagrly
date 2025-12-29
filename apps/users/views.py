from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from apps.common.permissions import IsOwnerOrAdmin

# SimpleJWT imports for custom token behavior
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claim for role: normalize to only 'admin' or 'user'
        role = 'admin' if (user.is_superuser or user.is_staff) else 'user'
        token['role'] = role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include role in the response payload for convenience (admin/user)
        data['role'] = 'admin' if (self.user.is_superuser or self.user.is_staff) else 'user'
        # Include user data
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'university': self.user.university,
            'faculty': self.user.faculty,
            'phone': self.user.phone,
            'role': 'admin' if (self.user.is_superuser or self.user.is_staff) else 'user',
            'free_ads_remaining': self.user.free_ads_remaining,
            'active_package': self.user.active_package.id if self.user.active_package else None,
            'package_expiry': self.user.package_expiry.isoformat() if self.user.package_expiry else None,
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def perform_update(self, serializer):
        serializer.save()

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user profile information for chatbot and other authenticated services."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dashboard(self, request):
        """Get user dashboard data including profile, ads count, etc."""
        user = request.user
        from apps.products.models import Product
        ads_count = Product.objects.filter(seller=user).count()
        active_ads = Product.objects.filter(seller=user, status='active').count()
        pending_ads = Product.objects.filter(seller=user, status='pending').count()
        wishlist_count = 0  # Will implement later
        from apps.wishlist.models import Wishlist
        wishlist_count = Wishlist.objects.filter(user=user).count()

        data = {
            'user': UserSerializer(user).data,
            'stats': {
                'total_ads': ads_count,
                'active_ads': active_ads,
                'pending_ads': pending_ads,
                'wishlist_count': wishlist_count,
            }
        }
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def assign_package(self, request, pk=None):
        """Admin endpoint to assign a subscription package to a user."""
        from apps.payments.models import Package
        from datetime import timedelta
        from django.utils import timezone
        
        user = self.get_object()
        package_id = request.data.get('package_id')
        
        if not package_id:
            return Response({'error': 'package_id is required'}, status=400)
        
        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return Response({'error': 'Package not found'}, status=404)
        
        # Assign package to user
        user.active_package = package
        user.package_expiry = timezone.now().date() + timedelta(days=package.duration_in_days)
        user.save()
        
        # Create notification for the user
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=user,
            notification_type='package_upgrade',
            title='🎉 Package Upgrade!',
            message=f'Congratulations! You have been upgraded to the {package.name} plan. You can now post up to {package.ad_limit} ads and enjoy premium features for {package.duration_in_days} days!'
        )
        
        return Response({
            'success': True,
            'message': f'User {user.username} upgraded to {package.name}',
            'user': UserSerializer(user).data
        })
