from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    active_package_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id','username','email','password','first_name','last_name','university','faculty','phone','role','is_staff','is_superuser','free_ads_remaining','active_package','active_package_name','package_expiry','is_email_verified','created_at','updated_at')
        read_only_fields = ('id','role','is_staff','is_superuser','free_ads_remaining','active_package_name','is_email_verified','created_at','updated_at')
    
    def get_role(self, obj):
        """Compute role dynamically based on is_staff or is_superuser, matching CustomTokenObtainPairSerializer logic"""
        return 'admin' if (obj.is_superuser or obj.is_staff) else 'user'

    def get_active_package_name(self, obj):
        """Return the name of the active package if one exists"""
        return obj.active_package.name if obj.active_package else None

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RegisterRequestSerializer(serializers.ModelSerializer):
    """Serializer for initial registration request - creates unverified user"""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'university', 'faculty', 'phone', 'governorate', 'location')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """Check that email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Check that username is unique"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_email_verified = False
        user.save()
        return user


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=4, max_length=4)
    
    def validate_otp(self, value):
        """Ensure OTP is numeric"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be 4 digits.")
        return value


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP"""
    email = serializers.EmailField(required=True)
