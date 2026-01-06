from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .serializers import UserSerializer, RegisterRequestSerializer, OTPVerifySerializer, ResendOTPSerializer
from .email_utils import generate_otp, send_otp_email
from apps.common.permissions import IsOwnerOrAdmin

# SimpleJWT imports for custom token behavior
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

# OTP expiry time in minutes
OTP_EXPIRY_MINUTES = 10


class EmailBackend(ModelBackend):
    """Custom authentication backend that uses email instead of username"""
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        return None


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force email field
        self.fields.pop('username', None)
        if 'email' not in self.fields:
            from rest_framework import serializers
            self.fields['email'] = serializers.EmailField()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = 'user'
        return token

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError('Must include "email" and "password".')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
             raise self.fail('no_active_account')
        
        if not user.check_password(password):
             raise self.fail('no_active_account')
        
        if not user.is_active:
             raise self.fail('no_active_account')
             
        # Strict Verification Check for Users
        if not user.is_email_verified:
            from rest_framework import serializers
            raise serializers.ValidationError({
                'detail': 'Email not verified. Please verify your email via OTP before logging in.',
                'email_not_verified': True
            })
            
        self.user = user
        refresh = self.get_token(self.user)
        
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': 'user',
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'is_email_verified': self.user.is_email_verified,
            }
        }
        return data


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Default username_field is 'username'
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = 'admin'
        return token

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
             raise serializers.ValidationError('Must include "username" and "password".')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
             raise self.fail('no_active_account')
        
        if not user.check_password(password):
             raise self.fail('no_active_account')
        
        if not user.is_active:
             raise self.fail('no_active_account')

        # Admin Access Check
        if not (user.is_superuser or user.is_staff):
             raise serializers.ValidationError('Access denied. Admin privileges required.')
             
        # NO Email Verification Check for Admins
        
        self.user = user
        refresh = self.get_token(self.user)
        
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': 'admin',
            'user': {
                 'id': self.user.id,
                 'username': self.user.username,
                 'email': self.user.email,
                 'role': 'admin'
            }
        }
        return data


class UserLoginView(TokenObtainPairView):
    serializer_class = UserTokenObtainPairSerializer

class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer


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
        elif self.action in ['register_request', 'verify_otp', 'resend_otp']:
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register_request(self, request):
        """
        Initial registration endpoint.
        Creates user with is_email_verified=False, generates OTP, sends email.
        """
        serializer = RegisterRequestSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate OTP and save to user
            otp = generate_otp()
            user.email_otp = otp
            user.email_otp_created_at = timezone.now()
            user.save()
            
            # Send OTP email
            try:
                send_otp_email(user.email, otp)
            except Exception as e:
                # Log error but don't fail the registration
                print(f"Error sending OTP email: {e}")
            
            return Response({
                'success': True,
                'message': 'Registration successful. Please check your email for the verification code.',
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def verify_otp(self, request):
        """
        Verify OTP and activate user account.
        """
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if already verified
            if user.is_email_verified:
                return Response({
                    'success': True,
                    'message': 'Email is already verified.'
                }, status=status.HTTP_200_OK)
            
            # Check OTP expiry
            if user.email_otp_created_at:
                expiry_time = user.email_otp_created_at + timedelta(minutes=OTP_EXPIRY_MINUTES)
                if timezone.now() > expiry_time:
                    return Response({
                        'success': False,
                        'error': 'OTP has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify OTP
            if user.email_otp != otp:
                return Response({
                    'success': False,
                    'error': 'Invalid OTP. Please try again.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark email as verified and clear OTP
            user.is_email_verified = True
            user.email_otp = None
            user.email_otp_created_at = None
            user.save()
            
            return Response({
                'success': True,
                'message': 'Email verified successfully! You can now log in.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def resend_otp(self, request):
        """
        Resend OTP to user's email.
        """
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if already verified
            if user.is_email_verified:
                return Response({
                    'success': True,
                    'message': 'Email is already verified.'
                }, status=status.HTTP_200_OK)
            
            # Generate new OTP
            otp = generate_otp()
            user.email_otp = otp
            user.email_otp_created_at = timezone.now()
            user.save()
            
            # Send OTP email
            try:
                send_otp_email(user.email, otp)
            except Exception as e:
                print(f"Error sending OTP email: {e}")
                return Response({
                    'success': False,
                    'error': 'Failed to send OTP email. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'message': 'OTP sent successfully. Please check your email.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

