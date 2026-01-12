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
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


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
        elif self.action == 'list':
            return [permissions.IsAuthenticated()]
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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def remove_package(self, request, pk=None):
        """Admin endpoint to remove subscription package from a user (downgrade to free)."""
        user = self.get_object()
        
        # Remove package from user and reset to free tier limits
        user.active_package = None
        user.package_expiry = None
        user.free_ads_remaining = 3  # Reset to free tier default
        user.save()
        
        # Create notification for the user
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=user,
            notification_type='package_downgrade',
            title='Package Change',
            message='Your subscription has been changed to the Free tier. You can continue using basic features.'
        )
        
        return Response({
            'success': True,
            'message': f'User {user.username} downgraded to Free tier',
            'user': UserSerializer(user).data
        })

from rest_framework.views import APIView
from google.oauth2 import id_token
from google.auth.transport import requests

class GoogleLoginView(APIView):
    """
    Login with Google ID Token.
    Verifies the token with Google and returns access/refresh tokens.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token
            # Note: In production you should specify the expected audience (client_id)
            # id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
            idinfo = id_token.verify_oauth2_token(token, requests.Request())

            if 'email' not in idinfo:
               return Response({'error': 'Invalid token: Email not found'}, status=status.HTTP_400_BAD_REQUEST)
            
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            
            # Find or Create User
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create user
                username = email.split('@')[0]
                # Ensure unique username
                if User.objects.filter(username=username).exists():
                    import uuid
                    username = f"{username}_{uuid.uuid4().hex[:4]}"
                    
                user = User.objects.create(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_email_verified=True # Google users are verified
                )
                user.set_unusable_password()
                user.save()
            
            # If user exists but is_email_verified is False (maybe old unverified account), verify it now
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save()

            # Generate tokens
            refresh = UserTokenObtainPairSerializer.get_token(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': 'user', # Or determine dynamically
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'username': user.username,
                    'is_email_verified': user.is_email_verified,
                }
            }
            return Response(data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'error': f'Invalid token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Google Login Error: {e}")
            return Response({'error': 'Google authentication failed'}, status=status.HTTP_400_BAD_REQUEST)
