from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wishlist
from .serializers import WishlistSerializer
from apps.common.permissions import IsOwnerOrAdmin

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product__category', 'product__seller')

    @action(detail=False, methods=['delete'], url_path='remove/(?P<product_id>[^/.]+)')
    def remove_by_product(self, request, product_id=None):
        """Remove product from wishlist by product ID (not wishlist item ID)"""
        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        wishlist_item = Wishlist.objects.filter(user=request.user, product_id=product_id).first()
        
        if wishlist_item:
            wishlist_item.delete()
            return Response({'status': 'removed', 'product_id': int(product_id)}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Item not in wishlist'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle product in wishlist"""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if product exists
            from apps.products.models import Product
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if already in wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()

        if wishlist_item:
            # Remove
            wishlist_item.delete()
            return Response({'status': 'removed', 'product_id': product_id}, status=status.HTTP_200_OK)
        else:
            # Add
            item = Wishlist.objects.create(user=request.user, product=product)
            serializer = self.get_serializer(item)
            return Response({'status': 'added', 'item': serializer.data}, status=status.HTTP_201_CREATED)

