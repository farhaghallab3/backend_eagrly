from rest_framework import viewsets, permissions
from .models import Package, Payment
from .serializers import PackageSerializer, PaymentSerializer
from apps.common.permissions import IsAdminOrReadOnly

class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAdminOrReadOnly]

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
