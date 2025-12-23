from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ('id','username','email','password','first_name','last_name','university','faculty','phone','role','free_ads_remaining','active_package','package_expiry','created_at','updated_at')
        read_only_fields = ('id','free_ads_remaining','created_at','updated_at')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
