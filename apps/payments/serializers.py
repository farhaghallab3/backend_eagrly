from rest_framework import serializers
from .models import Package, Payment

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    package_name = serializers.CharField(source='package.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_name', 'package', 'package_name', 
                  'payment_method', 'amount', 'start_date', 'expiry_date', 
                  'status', 'transaction_id']
        read_only_fields = ('start_date',)
    
    def get_user_name(self, obj):
        if obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.username

