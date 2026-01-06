from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.SerializerMethodField()
    reported_user_name = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('created_at', 'reporter')
    
    def get_reporter_name(self, obj):
        return obj.reporter.username if obj.reporter else None
    
    def get_reported_user_name(self, obj):
        return obj.reported_user.username if obj.reported_user else None
    
    def get_product_name(self, obj):
        return obj.product.title if obj.product else None
