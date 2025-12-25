from rest_framework import viewsets, permissions
from .models import Wishlist
from .serializers import WishlistSerializer
from apps.common.permissions import IsOwnerOrAdmin

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product__category', 'product__seller')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
